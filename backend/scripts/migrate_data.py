#!/usr/bin/env python3
"""
Main migration orchestrator: WordPress MySQL -> PostgreSQL (Snob Group platform).

Runs migrations in order: roles, users, products, categories, orders,
subscriptions, memberships, wallet, media, bookings.

Usage:
    python -m scripts.migrate_data [--force] [--skip-completed]

Environment:
    SOURCE_MYSQL_URL - MySQL connection string (e.g. mysql://user:pass@host:3306/db)
    DATABASE_URL     - PostgreSQL connection string (e.g. postgresql+asyncpg://...)
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add scripts directory to path for migration_utils and script imports
_scripts_dir = Path(__file__).resolve().parent
_backend_dir = _scripts_dir.parent
sys.path.insert(0, str(_scripts_dir))
sys.path.insert(0, str(_backend_dir))

from migration_utils import (
    get_mysql_url,
    get_postgres_url,
    postgres_pool,
    setup_logging,
    ensure_migration_tracker,
    is_migration_complete,
    mark_migration_complete,
)

logger = setup_logging()

MIGRATION_ORDER = [
    ("users", "migrate_users"),       # Includes roles setup
    ("products", "migrate_products"), # Includes categories
    ("orders", "migrate_orders"),
    ("subscriptions", "migrate_subscriptions"),  # Includes memberships
    ("wallet", "migrate_wallet"),
    ("media", "migrate_media"),
    ("bookings", "migrate_bookings"),
    ("redirects", "generate_redirects"),
]


async def run_migration(
    pool, module_name: str, step_name: str, force: bool, skip_completed: bool
):
    """Run a single migration step."""
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            module_name,
            Path(__file__).parent / f"{module_name}.py",
        )
        if not spec or not spec.loader:
            logger.warning("Could not load %s", module_name)
            return True
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        run_fn = getattr(module, "run", None)
        if not run_fn:
            logger.warning("Migration %s has no run() function, skipping", step_name)
            return True
        result = await run_fn(pool=pool, force=force, skip_completed=skip_completed)
        records = result.get("records_migrated", 0) if isinstance(result, dict) else 0
        await mark_migration_complete(pool, step_name, records_migrated=records)
        return True
    except ImportError as e:
        logger.error("Failed to import %s: %s", module_name, e)
        return False
    except Exception as e:
        logger.exception("Migration %s failed: %s", step_name, e)
        return False


async def main():
    parser = argparse.ArgumentParser(description="WordPress to PostgreSQL migration")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run migrations even if marked complete",
    )
    parser.add_argument(
        "--skip-completed",
        action="store_true",
        default=True,
        help="Skip migrations already marked complete (default: True)",
    )
    parser.add_argument(
        "--no-skip-completed",
        action="store_false",
        dest="skip_completed",
        help="Run all migrations regardless of completion status",
    )
    args = parser.parse_args()

    # Validate env
    try:
        get_mysql_url()
        get_postgres_url()
    except ValueError as e:
        logger.error("%s", e)
        sys.exit(1)

    logger.info("Starting migration: WordPress MySQL -> PostgreSQL")
    logger.info("Migration order: %s", [s for _, s in MIGRATION_ORDER])

    async with postgres_pool() as pool:
        await ensure_migration_tracker(pool)

        for step_name, module_name in MIGRATION_ORDER:
            if args.skip_completed and not args.force:
                if await is_migration_complete(pool, step_name):
                    logger.info("[SKIP] %s (already completed)", step_name)
                    continue

            logger.info("[START] %s", step_name)
            success = await run_migration(
                pool, module_name, step_name, args.force, args.skip_completed
            )
            if not success:
                logger.error("Migration failed at step: %s", step_name)
                sys.exit(1)
            logger.info("[DONE] %s", step_name)

    logger.info("All migrations completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
