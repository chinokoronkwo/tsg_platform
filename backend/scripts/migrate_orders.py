#!/usr/bin/env python3
"""
Migrate orders from WooCommerce to PostgreSQL.

Reads from agh_posts (post_type='shop_order') or agh_wc_orders (HPOS),
agh_woocommerce_order_items, agh_woocommerce_order_itemmeta.
Maps to orders and order_items. Migrates billing/shipping addresses from order meta.
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

# WooCommerce order status -> new status
ORDER_STATUS_MAP = {
    "wc-pending": "pending",
    "wc-processing": "processing",
    "wc-on-hold": "pending",
    "wc-completed": "completed",
    "wc-cancelled": "cancelled",
    "wc-refunded": "refunded",
    "wc-failed": "failed",
    "pending": "pending",
    "processing": "processing",
    "on-hold": "pending",
    "completed": "completed",
    "cancelled": "cancelled",
    "refunded": "refunded",
    "failed": "failed",
}


def _decimal(val) -> Decimal:
    if val is None or val == "":
        return Decimal("0")
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal("0")


def _int(val) -> int:
    if val is None or val == "":
        return 0
    try:
        return int(float(val))
    except Exception:
        return 0


def _address_from_meta(meta: dict) -> dict | None:
    """Build address dict from WooCommerce order meta."""
    first = meta.get("_billing_first_name") or meta.get("_shipping_first_name") or ""
    last = meta.get("_billing_last_name") or meta.get("_shipping_last_name") or ""
    addr1 = meta.get("_billing_address_1") or meta.get("_shipping_address_1") or ""
    addr2 = meta.get("_billing_address_2") or meta.get("_shipping_address_2") or ""
    city = meta.get("_billing_city") or meta.get("_shipping_city") or ""
    state = meta.get("_billing_state") or meta.get("_shipping_state") or ""
    postcode = meta.get("_billing_postcode") or meta.get("_shipping_postcode") or ""
    country = meta.get("_billing_country") or meta.get("_shipping_country") or ""
    if not any([first, last, addr1, city]):
        return None
    return {
        "first_name": first[:100],
        "last_name": last[:100],
        "address_1": addr1[:200],
        "address_2": (addr2 or "")[:200],
        "city": city[:100],
        "state": state[:100],
        "postcode": postcode[:20],
        "country": country[:2],
    }


async def run(
    pool=None,
    force: bool = False,
    skip_completed: bool = True,
) -> dict:
    """Run order migration."""
    if pool is None:
        async with postgres_pool() as p:
            return await _run_impl(p, force, skip_completed)
    return await _run_impl(pool, force, skip_completed)


async def _run_impl(pool, force: bool, skip_completed: bool) -> dict:
    if skip_completed and not force and await is_migration_complete(pool, "orders"):
        logger.info("Orders migration already complete, skipping")
        return {"records_migrated": 0}

    # Build user id mapping: wp_user_id -> pg_user_id (by email)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, email FROM users"
        )
        email_to_id = {r["email"]: r["id"] for r in rows}

    # Build product slug -> id mapping and wp_product_id -> slug
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, slug FROM products")
        slug_to_id = {r["slug"]: r["id"] for r in rows}

    migrated = 0
    skipped = 0
    errors = 0

    async with mysql_connection() as mysql_conn:
        # Try HPOS first (wc_orders), fallback to posts
        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            try:
                await cur.execute(
                    f"""
                    SELECT id, customer_id, status, total_amount, currency,
                           date_created_gmt, billing_email
                    FROM {WP_PREFIX}wc_orders
                    WHERE type = 'shop_order'
                    ORDER BY id
                    """
                )
                wp_orders = await cur.fetchall()
                use_hpos = True
            except Exception:
                use_hpos = False
                wp_orders = []

        if not use_hpos:
            async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"""
                    SELECT p.ID as id, p.post_date as date_created_gmt, p.post_status as status
                    FROM {WP_PREFIX}posts p
                    WHERE p.post_type = 'shop_order'
                    ORDER BY p.ID
                    """
                )
                wp_orders = await cur.fetchall()

        order_ids = [o["id"] for o in wp_orders]

        if not order_ids:
            logger.info("No orders found")
            return {"records_migrated": 0}

        placeholders = ",".join(["%s"] * len(order_ids))

        # Order meta (for posts-based)
        meta_by_order = {}
        if not use_hpos:
            async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"""
                    SELECT post_id as order_id, meta_key, meta_value
                    FROM {WP_PREFIX}postmeta
                    WHERE post_id IN ({placeholders})
                    """,
                    order_ids,
                )
                for r in await cur.fetchall():
                    oid = r["order_id"]
                    if oid not in meta_by_order:
                        meta_by_order[oid] = {}
                    meta_by_order[oid][r["meta_key"]] = r["meta_value"]

        # For HPOS, meta might be in wc_orders_meta
        if use_hpos:
            try:
                async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(
                        f"""
                        SELECT order_id, meta_key, meta_value
                        FROM {WP_PREFIX}wc_orders_meta
                        WHERE order_id IN ({placeholders})
                        """,
                        order_ids,
                    )
                    for r in await cur.fetchall():
                        oid = r["order_id"]
                        if oid not in meta_by_order:
                            meta_by_order[oid] = {}
                        meta_by_order[oid][r["meta_key"]] = r["meta_value"]
            except Exception:
                pass

        # Order items
        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"""
                SELECT order_item_id, order_id, order_item_name, order_item_type
                FROM {WP_PREFIX}woocommerce_order_items
                WHERE order_id IN ({placeholders}) AND order_item_type = 'line_item'
                """,
                order_ids,
            )
            item_rows = await cur.fetchall()

        item_ids = [i["order_item_id"] for i in item_rows]
        item_placeholders = ",".join(["%s"] * len(item_ids)) if item_ids else "0"

        item_meta = {}
        if item_ids:
            async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"""
                    SELECT order_item_id, meta_key, meta_value
                    FROM {WP_PREFIX}woocommerce_order_itemmeta
                    WHERE order_item_id IN ({item_placeholders})
                    """,
                    item_ids,
                )
                for r in await cur.fetchall():
                    iid = r["order_item_id"]
                    if iid not in item_meta:
                        item_meta[iid] = {}
                    item_meta[iid][r["meta_key"]] = r["meta_value"]

        # Build wp_product_id -> slug for order items
        wp_product_ids = set()
        for imeta in item_meta.values():
            pid = imeta.get("_product_id")
            if pid:
                wp_product_ids.add(int(pid))
        wp_id_to_slug = {}
        if wp_product_ids:
            pid_ph = ",".join(["%s"] * len(wp_product_ids))
            async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    f"""
                    SELECT ID, post_name FROM {WP_PREFIX}posts
                    WHERE ID IN ({pid_ph}) AND post_type IN ('product', 'product_variation')
                    """,
                    list(wp_product_ids),
                )
                for r in await cur.fetchall():
                    wp_id_to_slug[r["ID"]] = r["post_name"] or ""

    async with pool.acquire() as pg_conn:
        for i, wo in enumerate(wp_orders):
            try:
                order_id = wo["id"]
                existing = await pg_conn.fetchrow(
                    "SELECT id FROM orders WHERE id = $1", order_id
                )
                if existing:
                    skipped += 1
                    continue

                meta = meta_by_order.get(order_id, {})
                if use_hpos:
                    user_id = email_to_id.get(wo.get("billing_email", ""))
                    total = _decimal(wo.get("total_amount", 0))
                    status_raw = wo.get("status", "pending")
                    date_created = wo.get("date_created_gmt")
                else:
                    user_id = email_to_id.get(meta.get("_billing_email", ""))
                    total = _decimal(meta.get("_order_total", 0))
                    status_raw = wo.get("status", "wc-pending")
                    date_created = wo.get("date_created_gmt")

                if not user_id:
                    user_id = 1  # Fallback to first user if guest

                status = ORDER_STATUS_MAP.get(
                    status_raw.replace(" ", "").lower(),
                    "pending",
                )

                if isinstance(date_created, str):
                    try:
                        date_created = datetime.fromisoformat(
                            date_created.replace(" ", "T")
                        )
                    except ValueError:
                        date_created = datetime.now(timezone.utc)
                if date_created and date_created.tzinfo is None:
                    date_created = date_created.replace(tzinfo=timezone.utc)

                billing = _address_from_meta(
                    {**meta, "_billing_first_name": meta.get("_billing_first_name")}
                )
                shipping = _address_from_meta(
                    {**meta, "_shipping_first_name": meta.get("_shipping_first_name")}
                )

                await pg_conn.execute(
                    """
                    INSERT INTO orders (
                        id, user_id, status, currency, subtotal, tax_total,
                        discount_total, fee_total, total, billing_address,
                        shipping_address, customer_note, created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $13)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    order_id,
                    user_id,
                    status,
                    meta.get("_order_currency", "USD")[:3],
                    _decimal(meta.get("_order_subtotal", total)),
                    _decimal(meta.get("_order_tax", 0)),
                    _decimal(meta.get("_cart_discount", 0)),
                    Decimal("0"),
                    total,
                    billing,
                    shipping,
                    meta.get("_customer_note"),
                    date_created or datetime.now(timezone.utc),
                )

                # Order items
                for oi in item_rows:
                    if oi["order_id"] != order_id:
                        continue
                    imeta = item_meta.get(oi["order_item_id"], {})
                    wp_product_id = _int(imeta.get("_product_id"))
                    qty = _int(imeta.get("_qty", 1))
                    line_total = _decimal(imeta.get("_line_total", 0))
                    unit_price = _decimal(imeta.get("_line_subtotal", line_total)) / qty if qty else Decimal("0")

                    # Map wp product id -> slug -> pg product id
                    slug = wp_id_to_slug.get(wp_product_id, "") or imeta.get("_product_slug", "")
                    pg_product_id = slug_to_id.get(slug) if slug else None

                    await pg_conn.execute(
                        """
                        INSERT INTO order_items (
                            order_id, product_id, name, sku, quantity,
                            unit_price, total, metadata_json
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                        order_id,
                        pg_product_id or 1,  # Fallback; use first product if missing
                        (oi["order_item_name"] or "Item")[:300],
                        imeta.get("_sku"),
                        qty,
                        unit_price,
                        line_total,
                        {"wp_order_item_id": oi["order_item_id"]},
                    )

                migrated += 1
                if (i + 1) % 100 == 0:
                    logger.info("Migrated %d of %d orders", i + 1, len(wp_orders))

            except Exception as e:
                logger.exception("Error migrating order ID %s: %s", wo.get("id"), e)
                errors += 1

    # Update orders sequence for future inserts
    if migrated > 0:
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    SELECT setval(
                        pg_get_serial_sequence('orders', 'id'),
                        COALESCE((SELECT MAX(id) FROM orders), 1)
                    )
                    """
                )
        except Exception as e:
            logger.warning("Could not update orders sequence: %s", e)

    logger.info(
        "Orders migration complete: %d migrated, %d skipped, %d errors",
        migrated,
        skipped,
        errors,
    )
    return {"records_migrated": migrated, "skipped": skipped, "errors": errors}


if __name__ == "__main__":
    asyncio.run(run())
