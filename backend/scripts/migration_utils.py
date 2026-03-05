"""Shared utilities for WordPress to PostgreSQL migration scripts."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import aiomysql
import asyncpg
from dotenv import load_dotenv

# Load .env from backend directory
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# WordPress table prefix
WP_PREFIX = "agh_"

# Migration tracking table
MIGRATION_TRACKER_TABLE = "migration_tracker"


def get_mysql_url() -> str:
    """Get MySQL connection URL from SOURCE_MYSQL_URL env var."""
    url = os.getenv("SOURCE_MYSQL_URL")
    if not url:
        raise ValueError(
            "SOURCE_MYSQL_URL environment variable is required. "
            "Example: mysql://user:pass@host:3306/dbname"
        )
    return url


def get_postgres_url() -> str:
    """Get PostgreSQL connection URL from DATABASE_URL env var."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError(
            "DATABASE_URL environment variable is required. "
            "Example: postgresql+asyncpg://user:pass@host:5432/dbname"
        )
    # asyncpg uses postgresql:// not postgresql+asyncpg://
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


def _parse_mysql_url(url: str) -> dict:
    """Parse MySQL URL into connection kwargs."""
    from urllib.parse import urlparse, unquote

    if not url.startswith("mysql"):
        url = f"mysql://{url}"
    parsed = urlparse(url)
    db = (parsed.path or "/").lstrip("/").split("?")[0] or None
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username) if parsed.username else "root",
        "password": unquote(parsed.password) if parsed.password else None,
        "db": db,
    }


@asynccontextmanager
async def mysql_connection():
    """Context manager for MySQL connection using aiomysql."""
    url = get_mysql_url()
    kwargs = _parse_mysql_url(url)
    conn = await aiomysql.connect(
        **kwargs,
        charset="utf8mb4",
    )
    try:
        yield conn
    finally:
        conn.close()


@asynccontextmanager
async def postgres_pool():
    """Context manager for PostgreSQL connection pool using asyncpg."""
    url = get_postgres_url()
    pool = await asyncpg.create_pool(url, min_size=1, max_size=5, command_timeout=300)
    try:
        yield pool
    finally:
        await pool.close()


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger for migration scripts."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("migration")


async def ensure_migration_tracker(pg_pool: asyncpg.Pool) -> None:
    """Create migration_tracker table if it doesn't exist."""
    async with pg_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS migration_tracker (
                migration_name VARCHAR(100) PRIMARY KEY,
                completed_at TIMESTAMPTZ DEFAULT NOW(),
                records_migrated INTEGER DEFAULT 0,
                details JSONB
            )
        """)


async def is_migration_complete(pg_pool: asyncpg.Pool, migration_name: str) -> bool:
    """Check if a migration has been completed."""
    async with pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT 1 FROM migration_tracker WHERE migration_name = $1",
            migration_name,
        )
        return row is not None


async def mark_migration_complete(
    pg_pool: asyncpg.Pool,
    migration_name: str,
    records_migrated: int = 0,
    details: dict | None = None,
) -> None:
    """Mark a migration as complete."""
    import json

    async with pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO migration_tracker (migration_name, records_migrated, details)
            VALUES ($1, $2, $3)
            ON CONFLICT (migration_name) DO UPDATE SET
                completed_at = NOW(),
                records_migrated = EXCLUDED.records_migrated,
                details = EXCLUDED.details
            """,
            migration_name,
            records_migrated,
            json.dumps(details) if details else None,
        )
