#!/usr/bin/env python3
"""
Migrate WooCommerce Subscriptions and Memberships to PostgreSQL.

- Subscriptions: agh_posts (post_type='shop_subscription') -> subscriptions
- Memberships: agh_posts (post_type='wc_user_membership') -> memberships
- Creates 4 membership plans: Founders ($15K), Signature ($20K), Prestige ($35K), Executive ($45K)
"""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal

import aiomysql

from migration_utils import (
    WP_PREFIX,
    mysql_connection,
    postgres_pool,
    setup_logging,
    is_migration_complete,
)

logger = setup_logging()

# Membership plans: name, slug, tier, price
MEMBERSHIP_PLANS = [
    ("Founders", "founders", "founders", Decimal("15000")),
    ("Signature", "signature", "signature", Decimal("20000")),
    ("Prestige", "prestige", "prestige", Decimal("35000")),
    ("Executive", "executive", "executive", Decimal("45000")),
]

# Subscription status mapping
SUBSCRIPTION_STATUS_MAP = {
    "active": "active",
    "on-hold": "paused",
    "cancelled": "cancelled",
    "expired": "expired",
    "pending": "active",
    "wc-active": "active",
    "wc-on-hold": "paused",
    "wc-cancelled": "cancelled",
    "wc-expired": "expired",
    "wc-pending": "active",
}


def _parse_dt(val):
    if not val:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val
    try:
        dt = datetime.fromisoformat(str(val).replace(" ", "T"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


async def ensure_membership_plans(pool) -> dict[str, int]:
    """Create the 4 membership plans; return slug -> plan_id."""
    plan_ids = {}
    async with pool.acquire() as conn:
        for sort_order, (name, slug, tier, price) in enumerate(MEMBERSHIP_PLANS, 1):
            row = await conn.fetchrow(
                "SELECT id FROM membership_plans WHERE slug = $1", slug
            )
            if row:
                plan_ids[slug] = row["id"]
            else:
                row = await conn.fetchrow(
                    """
                    INSERT INTO membership_plans (name, slug, tier, price, is_active, sort_order)
                    VALUES ($1, $2, $3, $4, true, $5)
                    ON CONFLICT (slug) DO UPDATE SET price = EXCLUDED.price
                    RETURNING id
                    """,
                    name,
                    slug,
                    tier,
                    price,
                    sort_order,
                )
                plan_ids[slug] = row["id"]
                logger.info("Created membership plan: %s (id=%s)", slug, row["id"])
    return plan_ids


async def run(
    pool=None,
    force: bool = False,
    skip_completed: bool = True,
) -> dict:
    """Run subscription and membership migration."""
    if pool is None:
        async with postgres_pool() as p:
            return await _run_impl(p, force, skip_completed)
    return await _run_impl(pool, force, skip_completed)


async def _run_impl(pool, force: bool, skip_completed: bool) -> dict:
    if skip_completed and not force and await is_migration_complete(
        pool, "subscriptions"
    ):
        logger.info("Subscriptions migration already complete, skipping")
        return {"records_migrated": 0}

    plan_ids = await ensure_membership_plans(pool)

    # User mapping: email -> pg user id
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, email FROM users")
        email_to_id = {r["email"]: r["id"] for r in rows}

    # WP user_id -> email (for subscription user lookup)
    wp_user_to_email = {}
    async with mysql_connection() as mconn:
        async with mconn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"SELECT ID, user_email FROM {WP_PREFIX}users"
            )
            for r in await cur.fetchall():
                wp_user_to_email[r["ID"]] = r["user_email"]

    sub_migrated = 0
    mem_migrated = 0
    errors = 0

    async with mysql_connection() as mysql_conn:
        # Subscriptions
        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"""
                SELECT p.ID, p.post_status, p.post_date, p.post_modified
                FROM {WP_PREFIX}posts p
                WHERE p.post_type = 'shop_subscription'
                ORDER BY p.ID
                """
            )
            wp_subs = await cur.fetchall()

        if wp_subs:
            sub_ids = [s["ID"] for s in wp_subs]
            ph = ",".join(["%s"] * len(sub_ids))

            async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"""
                    SELECT post_id, meta_key, meta_value
                    FROM {WP_PREFIX}postmeta
                    WHERE post_id IN ({ph})
                    """,
                    sub_ids,
                )
                meta_rows = await cur.fetchall()

            meta_by_sub = {}
            for r in meta_rows:
                pid = r["post_id"]
                if pid not in meta_by_sub:
                    meta_by_sub[pid] = {}
                meta_by_sub[pid][r["meta_key"]] = r["meta_value"]

        # Memberships
        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"""
                SELECT p.ID, p.post_status, p.post_date
                FROM {WP_PREFIX}posts p
                WHERE p.post_type = 'wc_user_membership'
                ORDER BY p.ID
                """
            )
            wp_mems = await cur.fetchall()

        mem_meta = {}
        if wp_mems:
            mem_ids = [m["ID"] for m in wp_mems]
            ph = ",".join(["%s"] * len(mem_ids))
            async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"""
                    SELECT post_id, meta_key, meta_value
                    FROM {WP_PREFIX}postmeta
                    WHERE post_id IN ({ph})
                    """,
                    mem_ids,
                )
                for r in await cur.fetchall():
                    pid = r["post_id"]
                    if pid not in mem_meta:
                        mem_meta[pid] = {}
                    mem_meta[pid][r["meta_key"]] = r["meta_value"]

    async with pool.acquire() as pg_conn:
        # Migrate subscriptions
        for wp in wp_subs:
            try:
                meta = meta_by_sub.get(wp["ID"], {})
                wp_user_id = int(meta.get("_customer_user", 0) or 0)
                if not wp_user_id:
                    continue
                user_id = email_to_id.get(wp_user_to_email.get(wp_user_id, ""))
                if not user_id:
                    continue

                product_id = int(meta.get("_product_id", 0) or 0)
                if not product_id:
                    product_id = 1  # Fallback

                status_raw = wp["post_status"] or meta.get("_subscription_status", "active")
                status = SUBSCRIPTION_STATUS_MAP.get(
                    status_raw.replace(" ", "").lower(), "active"
                )

                period_start = _parse_dt(meta.get("_schedule_start") or meta.get("_start_date"))
                period_end = _parse_dt(meta.get("_schedule_next_payment") or meta.get("_end_date"))
                created = _parse_dt(wp["post_date"])

                existing = await pg_conn.fetchrow(
                    "SELECT id FROM subscriptions WHERE id = $1", wp["ID"]
                )
                if existing:
                    continue

                await pg_conn.execute(
                    """
                    INSERT INTO subscriptions (
                        id, user_id, product_id, status,
                        current_period_start, current_period_end,
                        stripe_subscription_id, created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    wp["ID"],
                    user_id,
                    product_id,
                    status,
                    period_start,
                    period_end,
                    meta.get("_stripe_subscription_id"),
                    created or datetime.now(timezone.utc),
                )
                sub_migrated += 1
            except Exception as e:
                logger.exception("Error migrating subscription %s: %s", wp["ID"], e)
                errors += 1

        # Migrate memberships
        for wp in wp_mems:
            try:
                meta = mem_meta.get(wp["ID"], {})
                wp_user_id = int(meta.get("_user_id", 0) or 0)
                if not wp_user_id:
                    continue
                user_id = email_to_id.get(wp_user_to_email.get(wp_user_id, ""))
                if not user_id:
                    continue
                plan_id_val = meta.get("_plan_id") or "founders"
                if isinstance(plan_id_val, str) and plan_id_val.isdigit():
                    plan_slug = "founders"  # term_id, map to default
                else:
                    plan_slug = str(plan_id_val).lower()
                    if plan_slug not in plan_ids:
                        plan_slug = "founders"
                plan_id = plan_ids.get(plan_slug, list(plan_ids.values())[0])

                starts_at = _parse_dt(meta.get("_start_date") or wp["post_date"])
                expires_at = _parse_dt(meta.get("_end_date"))

                if not user_id:
                    continue

                existing = await pg_conn.fetchrow(
                    "SELECT id FROM memberships WHERE id = $1", wp["ID"]
                )
                if existing:
                    continue

                await pg_conn.execute(
                    """
                    INSERT INTO memberships (
                        id, user_id, plan_id, status, starts_at, expires_at, created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    wp["ID"],
                    user_id,
                    plan_id,
                    "active" if wp["post_status"] == "wcm-active" else "expired",
                    starts_at or datetime.now(timezone.utc),
                    expires_at,
                    _parse_dt(wp["post_date"]) or datetime.now(timezone.utc),
                )
                mem_migrated += 1
            except Exception as e:
                logger.exception("Error migrating membership %s: %s", wp["ID"], e)
                errors += 1

    logger.info(
        "Subscriptions: %d migrated. Memberships: %d migrated. Errors: %d",
        sub_migrated,
        mem_migrated,
        errors,
    )
    return {
        "records_migrated": sub_migrated + mem_migrated,
        "subscriptions": sub_migrated,
        "memberships": mem_migrated,
        "errors": errors,
    }


if __name__ == "__main__":
    asyncio.run(run())
