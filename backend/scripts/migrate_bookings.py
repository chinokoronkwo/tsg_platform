#!/usr/bin/env python3
"""
Migrate bookings from WordPress (if any) to PostgreSQL.

WordPress typically does not have a built-in booking system that maps to our schema.
This is a stub for custom booking plugins (e.g. Amelia, Bookly, WooCommerce Bookings).
"""

import asyncio

from migration_utils import (
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
    """Run booking migration (stub)."""
    if pool is None:
        async with postgres_pool() as p:
            return await _run_impl(p, force, skip_completed)
    return await _run_impl(pool, force, skip_completed)


async def _run_impl(pool, force: bool, skip_completed: bool) -> dict:
    if skip_completed and not force and await is_migration_complete(pool, "bookings"):
        logger.info("Bookings migration already complete, skipping")
        return {"records_migrated": 0}

    # No WordPress booking tables by default; extend if using a booking plugin
    logger.info("Bookings migration: no WordPress booking data found (stub)")
    return {"records_migrated": 0}


if __name__ == "__main__":
    asyncio.run(run())
