"""File upload security: validation, S3/R2 uploads, image processing."""

import uuid
from pathlib import Path
from typing import BinaryIO

from fastapi import UploadFile, HTTPException, status
from PIL import Image
import io

# MIME type whitelist
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
}
ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
}
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "text/csv",
}
ALLOWED_MIME_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES | ALLOWED_DOCUMENT_TYPES

# Extension -> MIME mapping for validation
EXTENSION_MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".txt": "text/plain",
    ".csv": "text/csv",
}

# Size limits in bytes
DEFAULT_MEDIA_MAX_SIZE = 50 * 1024 * 1024   # 50MB
DEFAULT_DOCUMENT_MAX_SIZE = 10 * 1024 * 1024  # 10MB


def _get_max_size(mime_type: str) -> int:
    """Return max file size based on MIME type."""
    if mime_type in ALLOWED_DOCUMENT_TYPES:
        return DEFAULT_DOCUMENT_MAX_SIZE
    return DEFAULT_MEDIA_MAX_SIZE


def _validate_extension_mime(filename: str, mime_type: str) -> bool:
    """Ensure file extension matches declared MIME type."""
    ext = Path(filename).suffix.lower()
    expected_mime = EXTENSION_MIME_MAP.get(ext)
    if not expected_mime:
        return False
    return expected_mime == mime_type


def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename with UUID to prevent path traversal."""
    ext = Path(original_filename).suffix.lower()
    safe_ext = ext if ext in EXTENSION_MIME_MAP else ""
    return f"{uuid.uuid4().hex}{safe_ext}"


async def validate_upload(
    file: UploadFile,
    max_size: int | None = None,
) -> tuple[bytes, str, str]:
    """
    Validate uploaded file: MIME type, size, extension.
    Returns (content, mime_type, safe_filename).
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )
    content = await file.read()
    mime_type = file.content_type or "application/octet-stream"
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed: {mime_type}",
        )
    if not _validate_extension_mime(file.filename, mime_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File extension does not match content type",
        )
    limit = max_size or _get_max_size(mime_type)
    if len(content) > limit:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {limit // (1024*1024)}MB",
        )
    safe_filename = generate_unique_filename(file.filename)
    return content, mime_type, safe_filename


def get_s3_client():
    """Get boto3 S3 client configured for R2/S3."""
    import boto3
    from ..core.config import get_settings
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL or None,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY or None,
        region_name="auto",
    )


async def upload_to_s3(
    content: bytes,
    key: str,
    content_type: str,
    bucket: str | None = None,
) -> str:
    """Upload bytes to S3/R2 and return public URL."""
    from ..core.config import get_settings
    settings = get_settings()
    bucket_name = bucket or settings.S3_BUCKET_NAME
    client = get_s3_client()
    client.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=content,
        ContentType=content_type,
    )
    if settings.S3_PUBLIC_URL:
        return f"{settings.S3_PUBLIC_URL.rstrip('/')}/{key}"
    return f"https://{bucket_name}.s3.amazonaws.com/{key}"


def generate_presigned_upload_url(
    key: str,
    content_type: str,
    expires_in: int = 3600,
    bucket: str | None = None,
) -> str:
    """Generate signed upload URL for client-side uploads."""
    from ..core.config import get_settings
    settings = get_settings()
    bucket_name = bucket or settings.S3_BUCKET_NAME
    client = get_s3_client()
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket_name, "Key": key, "ContentType": content_type},
        ExpiresIn=expires_in,
    )


def resize_thumbnail(
    content: bytes,
    max_width: int = 300,
    max_height: int = 300,
    quality: int = 85,
) -> bytes:
    """Resize image to thumbnail using Pillow."""
    img = Image.open(io.BytesIO(content))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()
