#!/usr/bin/env python3
"""
Generate 301 redirects from old WordPress URLs to new Next.js routes.

- Products: /product/{slug}/ -> /shop/{slug}
- Pages: /{slug}/ -> /{slug}
- Categories: /product-category/{slug}/ -> /shop?category={slug}
- My Account: /my-account/ -> /account

Inserts into redirects table.
"""

import asyncio

import aiomysql

from migration_utils import (
    WP_PREFIX,
    mysql_connection,
    postgres_pool,
    setup_logging,
    is_migration_complete,
)

logger = setup_logging()


async def run(
    pool=None,
    force: bool = False,
    skip_completed: bool = True,
) -> dict:
    """Generate and insert redirects."""
    if pool is None:
        async with postgres_pool() as p:
            return await _run_impl(p, force, skip_completed)
    return await _run_impl(pool, force, skip_completed)


async def _run_impl(pool, force: bool, skip_completed: bool) -> dict:
    if skip_completed and not force and await is_migration_complete(
        pool, "redirects"
    ):
        logger.info("Redirects already generated, skipping")
        return {"records_migrated": 0}

    redirects = []

    # Static redirects
    redirects.extend([
        ("/my-account/", "/account"),
        ("/my-account", "/account"),
        ("/cart/", "/shop/cart"),
        ("/cart", "/shop/cart"),
        ("/checkout/", "/shop/checkout"),
        ("/checkout", "/shop/checkout"),
    ])

    async with mysql_connection() as mysql_conn:
        # Products: /product/{slug}/
        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"""
                SELECT post_name FROM {WP_PREFIX}posts
                WHERE post_type = 'product' AND post_status = 'publish'
                """
            )
            for r in await cur.fetchall():
                slug = r["post_name"]
                if slug:
                    redirects.append((f"/product/{slug}/", f"/shop/{slug}"))
                    redirects.append((f"/product/{slug}", f"/shop/{slug}"))

        # Product categories: /product-category/{slug}/
        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"""
                SELECT t.slug FROM {WP_PREFIX}terms t
                JOIN {WP_PREFIX}term_taxonomy tt ON t.term_id = tt.term_id
                WHERE tt.taxonomy = 'product_cat'
                """
            )
            for r in await cur.fetchall():
                slug = r["slug"]
                if slug:
                    redirects.append(
                        (f"/product-category/{slug}/", f"/shop?category={slug}")
                    )
                    redirects.append(
                        (f"/product-category/{slug}", f"/shop?category={slug}")
                    )

        # Pages: /{slug}/
        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"""
                SELECT post_name FROM {WP_PREFIX}posts
                WHERE post_type = 'page' AND post_status = 'publish'
                """
            )
            for r in await cur.fetchall():
                slug = r["post_name"]
                if slug and slug not in ("my-account", "cart", "checkout"):
                    redirects.append((f"/{slug}/", f"/{slug}"))
                    redirects.append((f"/{slug}", f"/{slug}"))

    # Normalize source paths (leading slash, no trailing for consistency)
    def norm(path: str) -> str:
        p = path.strip()
        if not p.startswith("/"):
            p = "/" + p
        return p

    seen = set()
    inserted = 0
    async with pool.acquire() as pg_conn:
        for source, target in redirects:
            src = norm(source)
            if src in seen:
                continue
            seen.add(src)
            try:
                await pg_conn.execute(
                    """
                    INSERT INTO redirects (source_path, target_path, status_code, is_active)
                    VALUES ($1, $2, 301, true)
                    ON CONFLICT (source_path) DO UPDATE SET
                        target_path = EXCLUDED.target_path,
                        status_code = EXCLUDED.status_code,
                        is_active = EXCLUDED.is_active
                    """,
                    src[:500],
                    target[:500],
                )
                inserted += 1
            except Exception as e:
                logger.warning("Failed to insert redirect %s -> %s: %s", source, target, e)

    logger.info("Generated %d redirects", inserted)
    return {"records_migrated": inserted}


if __name__ == "__main__":
    asyncio.run(run())
