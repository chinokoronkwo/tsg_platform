#!/usr/bin/env python3
"""
Migrate products from WordPress/WooCommerce to PostgreSQL.

Reads from agh_posts (post_type IN ('product', 'product_variation')),
agh_postmeta, agh_term_relationships. Maps to products, product_categories,
product_categories_assoc, product_media. Categories: 44=Suit Snob, 46=Shoe Snob,
47=Snip Snob.
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

# WooCommerce product category term_ids
CATEGORY_TERM_IDS = {
    44: ("Suit Snob", "suit-snob"),
    46: ("Shoe Snob", "shoe-snob"),
    47: ("Snip Snob", "snip-snob"),
}

# Product type mapping
PRODUCT_TYPE_MAP = {
    "simple": "physical",
    "variable": "physical",
    "subscription": "subscription",
    "subscription_variation": "subscription",
    "grouped": "physical",
    "external": "physical",
    "default": "physical",
}

# Stock status mapping
STOCK_STATUS_MAP = {
    "instock": "in_stock",
    "outofstock": "out_of_stock",
    "onbackorder": "on_backorder",
}


async def ensure_categories(pool) -> dict[int, int]:
    """Ensure product categories exist; return wp_term_id -> pg_id."""
    cat_map = {}
    async with pool.acquire() as conn:
        for term_id, (name, slug) in CATEGORY_TERM_IDS.items():
            row = await conn.fetchrow(
                "SELECT id FROM product_categories WHERE slug = $1", slug
            )
            if row:
                cat_map[term_id] = row["id"]
            else:
                row = await conn.fetchrow(
                    """
                    INSERT INTO product_categories (name, slug, sort_order)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                    """,
                    name,
                    slug,
                    term_id,
                )
                cat_map[term_id] = row["id"]
    return cat_map


def _decimal(val) -> Decimal | None:
    if val is None or val == "":
        return None
    try:
        return Decimal(str(val))
    except Exception:
        return None


def _int(val) -> int | None:
    if val is None or val == "":
        return None
    try:
        return int(float(val))
    except Exception:
        return None


async def run(
    pool=None,
    force: bool = False,
    skip_completed: bool = True,
) -> dict:
    """Run product migration."""
    if pool is None:
        async with postgres_pool() as p:
            return await _run_impl(p, force, skip_completed)
    return await _run_impl(pool, force, skip_completed)


async def _run_impl(pool, force: bool, skip_completed: bool) -> dict:
    if skip_completed and not force and await is_migration_complete(pool, "products"):
        logger.info("Products migration already complete, skipping")
        return {"records_migrated": 0}

    cat_map = await ensure_categories(pool)

    migrated = 0
    skipped = 0
    errors = 0

    async with mysql_connection() as mysql_conn:
        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"""
                SELECT ID, post_title, post_name, post_content, post_excerpt,
                       post_status, post_date, post_parent
                FROM {WP_PREFIX}posts
                WHERE post_type IN ('product', 'product_variation')
                  AND post_status IN ('publish', 'draft', 'private')
                ORDER BY post_parent ASC, ID ASC
                """
            )
            wp_posts = await cur.fetchall()

        post_ids = [p["ID"] for p in wp_posts]
        placeholders = ",".join(["%s"] * len(post_ids))

        # Postmeta
        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"""
                SELECT post_id, meta_key, meta_value
                FROM {WP_PREFIX}postmeta
                WHERE post_id IN ({placeholders})
                """,
                post_ids,
            )
            meta_rows = await cur.fetchall()

        meta_by_post = {}
        for r in meta_rows:
            pid = r["post_id"]
            if pid not in meta_by_post:
                meta_by_post[pid] = {}
            meta_by_post[pid][r["meta_key"]] = r["meta_value"]

        # Term relationships (product -> category)
        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"""
                SELECT tr.object_id, tt.term_id, t.name, t.slug
                FROM {WP_PREFIX}term_relationships tr
                JOIN {WP_PREFIX}term_taxonomy tt ON tr.term_taxonomy_id = tt.term_taxonomy_id
                JOIN {WP_PREFIX}terms t ON tt.term_id = t.term_id
                WHERE tr.object_id IN ({placeholders})
                  AND tt.taxonomy = 'product_cat'
                """,
                post_ids,
            )
            term_rows = await cur.fetchall()

        # product_id -> [(term_id, name, slug)]
        terms_by_product = {}
        for r in term_rows:
            pid = r["object_id"]
            if pid not in terms_by_product:
                terms_by_product[pid] = []
            terms_by_product[pid].append((r["term_id"], r["name"], r["slug"]))

        # Product type from term taxonomy 'product_type'
        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"""
                SELECT tr.object_id, t.slug as type_slug
                FROM {WP_PREFIX}term_relationships tr
                JOIN {WP_PREFIX}term_taxonomy tt ON tr.term_taxonomy_id = tt.term_taxonomy_id
                JOIN {WP_PREFIX}terms t ON tt.term_id = t.term_id
                WHERE tr.object_id IN ({placeholders})
                  AND tt.taxonomy = 'product_type'
                """,
                post_ids,
            )
            type_rows = await cur.fetchall()

        type_by_product = {r["object_id"]: r["type_slug"] for r in type_rows}

    # Only migrate parent products (post_parent=0), not variations
    parent_products = [p for p in wp_posts if p["post_parent"] == 0]
    variations = {p["post_parent"]: p for p in wp_posts if p["post_parent"] != 0}

    async with pool.acquire() as pg_conn:
        for i, wp in enumerate(parent_products):
            try:
                slug = wp["post_name"] or f"product-{wp['ID']}"
                existing = await pg_conn.fetchrow(
                    "SELECT id FROM products WHERE slug = $1", slug
                )
                if existing:
                    skipped += 1
                    continue

                meta = meta_by_post.get(wp["ID"], {})
                price = _decimal(meta.get("_price")) or Decimal("0")
                sale_price = _decimal(meta.get("_sale_price"))
                sku = meta.get("_sku") or None
                stock = _int(meta.get("_stock"))
                stock_status = STOCK_STATUS_MAP.get(
                    (meta.get("_stock_status") or "instock").lower(),
                    "in_stock",
                )
                product_type = PRODUCT_TYPE_MAP.get(
                    type_by_product.get(wp["ID"], "simple"),
                    "physical",
                )
                status = "published" if wp["post_status"] == "publish" else "draft"

                post_date = wp["post_date"]
                if isinstance(post_date, str):
                    try:
                        post_date = datetime.fromisoformat(post_date.replace(" ", "T"))
                    except ValueError:
                        post_date = datetime.now(timezone.utc)
                if post_date and post_date.tzinfo is None:
                    post_date = post_date.replace(tzinfo=timezone.utc)

                await pg_conn.execute(
                    """
                    INSERT INTO products (
                        name, slug, description, short_description,
                        product_type, status, sku, price, sale_price,
                        stock_quantity, stock_status, manage_stock,
                        published_at, created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $14)
                    """,
                    (wp["post_title"] or "Untitled")[:300],
                    slug[:300],
                    wp["post_content"] or None,
                    wp["post_excerpt"] or None,
                    product_type,
                    status,
                    sku[:100] if sku else None,
                    price,
                    sale_price,
                    stock,
                    stock_status,
                    stock is not None,
                    post_date,
                )

                new_id = await pg_conn.fetchval(
                    "SELECT id FROM products WHERE slug = $1", slug
                )

                # Categories
                for term_id, _, _ in terms_by_product.get(wp["ID"], []):
                    if term_id in cat_map:
                        await pg_conn.execute(
                            """
                            INSERT INTO product_categories_assoc (product_id, category_id)
                            VALUES ($1, $2)
                            ON CONFLICT (product_id, category_id) DO NOTHING
                            """,
                            new_id,
                            cat_map[term_id],
                        )

                # Product images: _thumbnail_id, _product_image_gallery
                thumb_id = _int(meta.get("_thumbnail_id"))
                gallery = meta.get("_product_image_gallery", "")
                image_ids = [thumb_id] if thumb_id else []
                if gallery:
                    image_ids.extend(int(x) for x in gallery.split(",") if x.strip())
                image_ids = list(dict.fromkeys(image_ids))  # dedupe

                for sort_order, att_id in enumerate(image_ids):
                    if not att_id:
                        continue
                    # We'll add product_media after media migration; for now store att_id in metadata
                    # Or we can insert product_media with placeholder URL - media migration will update
                    # For idempotency, use wp attachment URL as placeholder
                    await pg_conn.execute(
                        """
                        INSERT INTO product_media (product_id, url, media_type, sort_order, is_featured)
                        VALUES ($1, $2, 'image', $3, $4)
                        """,
                        new_id,
                        f"__wp_attachment_{att_id}__",  # Placeholder for media migration
                        sort_order,
                        sort_order == 0,
                    )

                migrated += 1
                if (i + 1) % 50 == 0:
                    logger.info("Migrated %d of %d products", i + 1, len(parent_products))

            except Exception as e:
                logger.exception("Error migrating product ID %s: %s", wp["ID"], e)
                errors += 1

    logger.info(
        "Products migration complete: %d migrated, %d skipped, %d errors",
        migrated,
        skipped,
        errors,
    )
    return {"records_migrated": migrated, "skipped": skipped, "errors": errors}


if __name__ == "__main__":
    asyncio.run(run())
