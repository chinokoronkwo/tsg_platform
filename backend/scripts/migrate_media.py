#!/usr/bin/env python3
"""
Migrate media from WordPress (agh_posts post_type='attachment') to PostgreSQL media_library.

Maps attachment metadata to media_library. Outputs a media download list (source URLs)
for batch download to S3/R2. Generates URL mapping for old WP URLs -> new S3/R2 URLs.
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import aiomysql

from migration_utils import (
    WP_PREFIX,
    mysql_connection,
    postgres_pool,
    setup_logging,
    is_migration_complete,
)

logger = setup_logging()

# Output file for download list
MEDIA_DOWNLOAD_LIST = "media_download_list.json"
MEDIA_URL_MAPPING = "media_url_mapping.json"


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
    """Run media migration."""
    if pool is None:
        async with postgres_pool() as p:
            return await _run_impl(p, force, skip_completed)
    return await _run_impl(pool, force, skip_completed)


async def _run_impl(pool, force: bool, skip_completed: bool) -> dict:
    if skip_completed and not force and await is_migration_complete(pool, "media"):
        logger.info("Media migration already complete, skipping")
        return {"records_migrated": 0}

    # Default uploader for media without post_author
    default_uploader = 1

    download_list = []
    url_mapping = {}

    async with mysql_connection() as mysql_conn:
        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"""
                SELECT ID, post_title, post_name, post_mime_type, post_date, post_author, guid
                FROM {WP_PREFIX}posts
                WHERE post_type = 'attachment'
                ORDER BY ID
                """
            )
            attachments = await cur.fetchall()

        if not attachments:
            logger.info("No attachments found")
            return {"records_migrated": 0}

        att_ids = [a["ID"] for a in attachments]
        ph = ",".join(["%s"] * len(att_ids))

        async with mysql_conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                f"""
                SELECT post_id, meta_key, meta_value
                FROM {WP_PREFIX}postmeta
                WHERE post_id IN ({ph})
                """,
                att_ids,
            )
            meta_rows = await cur.fetchall()

        meta_by_att = {}
        for r in meta_rows:
            pid = r["post_id"]
            if pid not in meta_by_att:
                meta_by_att[pid] = {}
            meta_by_att[pid][r["meta_key"]] = r["meta_value"]

    # User mapping: wp user id -> pg user id
    wp_user_to_email = {}
    async with mysql_connection() as mconn:
        async with mconn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(f"SELECT ID, user_email FROM {WP_PREFIX}users")
            for r in await cur.fetchall():
                wp_user_to_email[r["ID"]] = r["user_email"]

    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, email FROM users")
        email_to_id = {r["email"]: r["id"] for r in rows}

    migrated = 0
    skipped = 0
    errors = 0

    async with pool.acquire() as pg_conn:
        for i, att in enumerate(attachments):
            try:
                att_id = att["ID"]
                meta = meta_by_att.get(att_id, {})

                # _wp_attached_file has relative path like "2024/01/image.jpg"
                attached_file = meta.get("_wp_attached_file", "")
                guid = att.get("guid", "")

                # Source URL for download (WordPress uploads URL)
                # guid is typically full URL; attached_file is relative
                source_url = guid if guid.startswith("http") else ""
                if not source_url and attached_file:
                    # Build URL from site - we don't have site URL, use placeholder
                    source_url = f"__uploads__/{attached_file}"

                filename = attached_file.split("/")[-1] if attached_file else att.get("post_name", f"attachment-{att_id}")
                original_filename = meta.get("_wp_attachment_metadata", "")
                if isinstance(original_filename, str) and "filename" in original_filename:
                    import ast
                    try:
                        # PHP serialized - simplified
                        pass
                    except Exception:
                        pass
                original_filename = filename

                mime_type = att.get("post_mime_type", "application/octet-stream")
                file_size = _int(meta.get("_wp_attachment_file_size")) or 0
                width = None
                height = None
                # _wp_attachment_metadata is often PHP serialized; skip complex parse

                alt_text = meta.get("_wp_attachment_image_alt", "")
                caption = att.get("post_excerpt", "") or ""

                uploader_id = email_to_id.get(
                    wp_user_to_email.get(att.get("post_author", 0), ""),
                    default_uploader,
                )

                # New URL placeholder - will be updated after S3 upload
                new_url = f"https://cdn.example.com/media/{att_id}/{filename}"

                # Idempotent: check by original filename or guid
                existing = await pg_conn.fetchrow(
                    """
                    SELECT id FROM media_library
                    WHERE original_filename = $1 OR url LIKE $2
                    """,
                    original_filename,
                    f"%{att_id}%",
                )
                if existing:
                    skipped += 1
                    url_mapping[source_url] = await pg_conn.fetchval(
                        "SELECT url FROM media_library WHERE id = $1", existing["id"]
                    )
                    continue

                await pg_conn.execute(
                    """
                    INSERT INTO media_library (
                        filename, original_filename, url, mime_type, file_size,
                        width, height, alt_text, caption, folder, uploaded_by, created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """,
                    filename[:300],
                    original_filename[:300],
                    new_url[:500],
                    mime_type[:100],
                    file_size or 0,
                    width,
                    height,
                    (alt_text or None)[:300] if alt_text else None,
                    (caption or None)[:500] if caption else None,
                    f"wp_import_{att_id}",
                    uploader_id,
                    _parse_dt(att.get("post_date")) or datetime.now(timezone.utc),
                )

                url_mapping[source_url] = new_url
                download_list.append({
                    "wp_attachment_id": att_id,
                    "source_url": source_url,
                    "filename": filename,
                    "mime_type": mime_type,
                    "target_key": f"media/{att_id}/{filename}",
                })
                migrated += 1

                if (i + 1) % 100 == 0:
                    logger.info("Migrated %d of %d media", i + 1, len(attachments))

            except Exception as e:
                logger.exception("Error migrating attachment %s: %s", att.get("ID"), e)
                errors += 1

    # Write download list and URL mapping
    scripts_dir = Path(__file__).resolve().parent
    with open(scripts_dir / MEDIA_DOWNLOAD_LIST, "w") as f:
        json.dump(download_list, f, indent=2)
    with open(scripts_dir / MEDIA_URL_MAPPING, "w") as f:
        json.dump(url_mapping, f, indent=2)

    logger.info(
        "Media migration: %d migrated, %d skipped, %d errors. Output: %s, %s",
        migrated,
        skipped,
        errors,
        MEDIA_DOWNLOAD_LIST,
        MEDIA_URL_MAPPING,
    )
    return {
        "records_migrated": migrated,
        "skipped": skipped,
        "errors": errors,
        "download_list_file": str(scripts_dir / MEDIA_DOWNLOAD_LIST),
        "url_mapping_file": str(scripts_dir / MEDIA_URL_MAPPING),
    }


if __name__ == "__main__":
    asyncio.run(run())
