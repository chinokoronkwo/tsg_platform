#!/usr/bin/env python3
"""
Migrate users from WordPress (agh_users, agh_usermeta) to PostgreSQL users table.

Maps: user_login->username, user_email->email, user_pass->hashed_password,
display_name->display_name, user_registered->created_at, first_name/last_name
from usermeta, billing_phone->phone. Sets must_reset_password=True for migrated
passwords. Maps WordPress roles to 14-role system. Creates social_accounts from
social login usermeta.
"""

import asyncio
from datetime import datetime, timezone

import aiomysql

from migration_utils import (
    WP_PREFIX,
    mysql_connection,
    postgres_pool,
    setup_logging,
    is_migration_complete,
)

logger = setup_logging()

# WordPress role slug -> new RoleType slug
WP_ROLE_MAP = {
    "administrator": "administrator",
    "editor": "editor",
    "author": "author",
    "contributor": "contributor",
    "subscriber": "subscriber",
    "customer": "customer",
    "shop_manager": "shop_manager",
    "gfb_customer": "gfb_customer",
    "gfb_staff": "gfb_staff",
    "sc_shop_manager": "sc_shop_manager",
    "sc_shop_accountant": "sc_shop_accountant",
    "sc_shop_worker": "sc_shop_worker",
    "sc_customer": "sc_customer",
    "seo_manager": "seo_manager",
}

# All 14 roles from schema
ROLE_SLUGS = list(WP_ROLE_MAP.values())

# Social login meta keys (provider -> meta_key pattern)
SOCIAL_META_KEYS = {
    "google": "_wc_social_login_google_identifier",
    "facebook": "_wc_social_login_facebook_identifier",
    "apple": "_wc_social_login_apple_identifier",
    "microsoft": "_wc_social_login_microsoft_identifier",
}


async def ensure_roles(pool) -> dict[str, int]:
    """Ensure all 14 roles exist; return slug->id mapping."""
    role_ids = {}
    async with pool.acquire() as conn:
        for slug in ROLE_SLUGS:
            name = slug.replace("_", " ").title()
            row = await conn.fetchrow(
                "SELECT id FROM roles WHERE slug = $1", slug
            )
            if row:
                role_ids[slug] = row["id"]
            else:
                row = await conn.fetchrow(
                    """
                    INSERT INTO roles (name, slug, is_default)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                    """,
                    name,
                    slug,
                    slug == "customer",
                )
                role_ids[slug] = row["id"]
                logger.info("Created role: %s (id=%s)", slug, row["id"])
    return role_ids


async def run(
    pool=None,
    force: bool = False,
    skip_completed: bool = True,
) -> dict:
    """Run user migration."""
    if pool is None:
        async with postgres_pool() as p:
            return await _run_impl(p, force, skip_completed)
    return await _run_impl(pool, force, skip_completed)


async def _run_impl(pool, force: bool, skip_completed: bool) -> dict:
    if skip_completed and not force and await is_migration_complete(pool, "users"):
        logger.info("Users migration already complete, skipping")
        return {"records_migrated": 0}

    role_ids = await ensure_roles(pool)

    migrated = 0
    skipped = 0
    errors = 0

    async with mysql_connection() as mysql_conn:
        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"""
                SELECT ID, user_login, user_email, user_pass, display_name,
                       user_registered, user_status
                FROM {WP_PREFIX}users
                ORDER BY ID
                """
            )
            wp_users = await cur.fetchall()

        # Fetch usermeta for all users
        user_ids = [u["ID"] for u in wp_users]
        placeholders = ",".join(["%s"] * len(user_ids))

        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"""
                SELECT user_id, meta_key, meta_value
                FROM {WP_PREFIX}usermeta
                WHERE user_id IN ({placeholders})
                """,
                user_ids,
            )
            meta_rows = await cur.fetchall()

        # Build meta lookup: user_id -> {meta_key: meta_value}
        meta_by_user = {}
        for r in meta_rows:
            uid = r["user_id"]
            if uid not in meta_by_user:
                meta_by_user[uid] = {}
            meta_by_user[uid][r["meta_key"]] = r["meta_value"]

        # Fetch WordPress capabilities (roles) - simplified
        wp_caps = {}
        for uid in user_ids:
            meta = meta_by_user.get(uid, {})
            caps_str = meta.get(f"{WP_PREFIX}capabilities", "") or ""
            if "administrator" in str(caps_str).lower():
                wp_caps[uid] = "administrator"
            elif "shop_manager" in str(caps_str).lower():
                wp_caps[uid] = "shop_manager"
            elif "customer" in str(caps_str).lower():
                wp_caps[uid] = "customer"
            elif "subscriber" in str(caps_str).lower():
                wp_caps[uid] = "subscriber"
            else:
                wp_caps[uid] = "customer"

    async with pool.acquire() as pg_conn:
        for i, wp in enumerate(wp_users):
            try:
                # Idempotent: check if user exists by email
                existing = await pg_conn.fetchrow(
                    "SELECT id FROM users WHERE email = $1", wp["user_email"]
                )
                if existing:
                    skipped += 1
                    if (i + 1) % 100 == 0:
                        logger.info("Migrated %d of %d (skipped %d)", i + 1, len(wp_users), skipped)
                    continue

                meta = meta_by_user.get(wp["ID"], {})
                first_name = (meta.get("first_name") or "")[:100]
                last_name = (meta.get("last_name") or "")[:100]
                phone = meta.get("billing_phone") or meta.get("phone", "")
                phone = (phone or None)[:20] if phone else None

                user_registered = wp["user_registered"]
                if isinstance(user_registered, str):
                    try:
                        user_registered = datetime.fromisoformat(
                            user_registered.replace(" ", "T")
                        )
                    except ValueError:
                        user_registered = datetime.now(timezone.utc)
                if user_registered and user_registered.tzinfo is None:
                    user_registered = user_registered.replace(tzinfo=timezone.utc)

                wp_role = wp_caps.get(wp["ID"], "customer")
                role_slug = WP_ROLE_MAP.get(wp_role, "customer")
                role_id = role_ids.get(role_slug, role_ids["customer"])

                await pg_conn.execute(
                    """
                    INSERT INTO users (
                        email, username, hashed_password, first_name, last_name,
                        display_name, phone, is_active, must_reset_password,
                        created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $10)
                    """,
                    wp["user_email"],
                    wp["user_login"] or None,
                    wp["user_pass"] or None,
                    first_name,
                    last_name,
                    (wp["display_name"] or wp["user_login"] or "")[:200],
                    phone,
                    True,
                    True,  # Force password reset on first login
                    user_registered or datetime.now(timezone.utc),
                )

                new_id = await pg_conn.fetchval(
                    "SELECT id FROM users WHERE email = $1", wp["user_email"]
                )

                # Assign role
                await pg_conn.execute(
                    """
                    INSERT INTO user_roles (user_id, role_id)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id, role_id) DO NOTHING
                    """,
                    new_id,
                    role_id,
                )

                # Social accounts
                for provider, meta_key in SOCIAL_META_KEYS.items():
                    provider_id = meta.get(meta_key)
                    if provider_id:
                        await pg_conn.execute(
                            """
                            INSERT INTO social_accounts (user_id, provider, provider_user_id, created_at)
                            VALUES ($1, $2, $3, NOW())
                            ON CONFLICT (provider, provider_user_id) DO NOTHING
                            """,
                            new_id,
                            provider,
                            str(provider_id),
                        )

                migrated += 1
                if (i + 1) % 100 == 0:
                    logger.info("Migrated %d of %d users", i + 1, len(wp_users))

            except Exception as e:
                logger.exception("Error migrating user ID %s: %s", wp["ID"], e)
                errors += 1

    logger.info(
        "Users migration complete: %d migrated, %d skipped, %d errors",
        migrated,
        skipped,
        errors,
    )
    return {"records_migrated": migrated, "skipped": skipped, "errors": errors}


if __name__ == "__main__":
    asyncio.run(run())
