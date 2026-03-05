#!/usr/bin/env python3
"""
Migrate TeraWallet / WooCommerce Wallet data to PostgreSQL.

Reads from:
- agh_usermeta (meta_key like '_woo_wallet_balance', '_terawallet_balance')
- agh_woo_wallet_transactions (if exists)
- agh_posts with post_type related to wallet (if used)

Creates wallet_accounts and wallet_transactions.
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

# Common wallet balance meta keys
WALLET_BALANCE_KEYS = (
    "_woo_wallet_balance",
    "_terawallet_balance",
    "woo_wallet_balance",
    "_current_woo_wallet_balance",
)


def _decimal(val) -> Decimal:
    if val is None or val == "":
        return Decimal("0")
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal("0")


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


async def run(
    pool=None,
    force: bool = False,
    skip_completed: bool = True,
) -> dict:
    """Run wallet migration."""
    if pool is None:
        async with postgres_pool() as p:
            return await _run_impl(p, force, skip_completed)
    return await _run_impl(pool, force, skip_completed)


async def _run_impl(pool, force: bool, skip_completed: bool) -> dict:
    if skip_completed and not force and await is_migration_complete(pool, "wallet"):
        logger.info("Wallet migration already complete, skipping")
        return {"records_migrated": 0}

    # User mapping: wp user id -> pg user id (by email)
    wp_user_to_email = {}
    async with mysql_connection() as mconn:
        async with mconn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"SELECT ID, user_email FROM {WP_PREFIX}users"
            )
            for r in await cur.fetchall():
                wp_user_to_email[r["ID"]] = r["user_email"]

    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, email FROM users")
        email_to_id = {r["email"]: r["id"] for r in rows}

    migrated_accounts = 0
    migrated_txns = 0
    errors = 0

    # 1. Wallet accounts from usermeta balance
    async with mysql_connection() as mysql_conn:
        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            keys_ph = ",".join(["%s"] * len(WALLET_BALANCE_KEYS))
            await cur.execute(
                f"""
                SELECT user_id, meta_key, meta_value
                FROM {WP_PREFIX}usermeta
                WHERE meta_key IN ({keys_ph})
                """,
                WALLET_BALANCE_KEYS,
            )
            balance_rows = await cur.fetchall()

        # user_id -> balance (take first non-zero)
        balances = {}
        for r in balance_rows:
            uid = r["user_id"]
            bal = _decimal(r["meta_value"])
            if uid not in balances or bal != 0:
                balances[uid] = bal

        # Check for woo_wallet_transactions table
        has_txn_table = False
        try:
            async with mysql_conn.cursor() as cur:
                await cur.execute(
                    f"SHOW TABLES LIKE '{WP_PREFIX}woo_wallet_transactions'"
                )
                has_txn_table = await cur.fetchone() is not None
        except Exception:
            pass

        txn_rows = []
        if has_txn_table:
            async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
                try:
                    await cur.execute(
                        f"""
                        SELECT transaction_id, user_id, type, amount, balance,
                               details, created_by, date
                        FROM {WP_PREFIX}woo_wallet_transactions
                        ORDER BY transaction_id
                        """
                    )
                    txn_rows = await cur.fetchall()
                except Exception as e:
                    logger.warning("Could not read woo_wallet_transactions: %s", e)

    async with pool.acquire() as pg_conn:
        for wp_user_id, balance in balances.items():
            if balance == 0 and wp_user_id not in [t.get("user_id") for t in txn_rows]:
                continue
            try:
                pg_user_id = email_to_id.get(wp_user_to_email.get(wp_user_id, ""))
                if not pg_user_id:
                    continue

                existing = await pg_conn.fetchrow(
                    "SELECT id FROM wallet_accounts WHERE user_id = $1", pg_user_id
                )
                if existing:
                    continue

                await pg_conn.execute(
                    """
                    INSERT INTO wallet_accounts (user_id, balance, allow_negative, created_at, updated_at)
                    VALUES ($1, $2, false, NOW(), NOW())
                    ON CONFLICT (user_id) DO UPDATE SET balance = EXCLUDED.balance, updated_at = NOW()
                    """,
                    pg_user_id,
                    balance,
                )
                migrated_accounts += 1
            except Exception as e:
                logger.exception("Error creating wallet for user %s: %s", wp_user_id, e)
                errors += 1

        # Wallet transactions
        wallet_ids = {}
        if txn_rows:
            rows = await pg_conn.fetch(
                "SELECT id, user_id FROM wallet_accounts"
            )
            wallet_ids = {r["user_id"]: r["id"] for r in rows}

        for txn in txn_rows:
            try:
                pg_user_id = email_to_id.get(
                    wp_user_to_email.get(txn.get("user_id", 0), "")
                )
                if not pg_user_id:
                    continue
                wallet_id = wallet_ids.get(pg_user_id)
                if not wallet_id:
                    continue

                # Idempotent: check by reference
                ref = f"wp_wallet_txn_{txn.get('transaction_id')}"
                existing = await pg_conn.fetchrow(
                    """
                    SELECT 1 FROM wallet_transactions
                    WHERE wallet_id = $1 AND description LIKE $2
                    """,
                    wallet_id,
                    f"%{ref}%",
                )
                if existing:
                    continue

                amount = _decimal(txn.get("amount", 0))
                balance_after = _decimal(txn.get("balance", 0))
                txn_type = (txn.get("type") or "credit").lower()
                if txn_type in ("debit", "withdrawal"):
                    amount = -abs(amount)
                else:
                    amount = abs(amount)

                date_val = _parse_dt(txn.get("date"))

                await pg_conn.execute(
                    """
                    INSERT INTO wallet_transactions (
                        wallet_id, amount, balance_after, transaction_type,
                        description, reference_type, reference_id, created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    wallet_id,
                    amount,
                    balance_after,
                    txn_type[:20],
                    f"{txn.get('details', 'Migrated')} [{ref}]",
                    "migration",
                    txn.get("transaction_id"),
                    date_val or datetime.now(timezone.utc),
                )
                migrated_txns += 1
            except Exception as e:
                logger.exception("Error migrating transaction %s: %s", txn.get("transaction_id"), e)
                errors += 1

    logger.info(
        "Wallet migration: %d accounts, %d transactions, %d errors",
        migrated_accounts,
        migrated_txns,
        errors,
    )
    return {
        "records_migrated": migrated_accounts + migrated_txns,
        "accounts": migrated_accounts,
        "transactions": migrated_txns,
        "errors": errors,
    }


if __name__ == "__main__":
    asyncio.run(run())
