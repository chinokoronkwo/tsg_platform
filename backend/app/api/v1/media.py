"""Media API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from ...core.database import get_db
from ...middleware.auth import get_current_user, require_staff
from ...models.user import User
from ...models.cms import Media

router = APIRouter()


class FolderCreate(BaseModel):
    name: str
    parent_id: int | None = None


@router.get("/")
async def list_media(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, description="Search by filename"),
    mime_type: str | None = Query(None),
    folder: str | None = Query(None),
) -> dict:
    """List media with pagination, search by filename, filter by mime_type and folder."""
    query = select(Media)
    count_query = select(func.count(Media.id))

    if search:
        search_term = f"%{search}%"
        search_filter = Media.filename.ilike(search_term) | Media.original_filename.ilike(search_term)
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    if mime_type:
        query = query.where(Media.mime_type == mime_type)
        count_query = count_query.where(Media.mime_type == mime_type)
    if folder:
        query = query.where(Media.folder == folder)
        count_query = count_query.where(Media.folder == folder)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Media.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [
            {
                "id": m.id,
                "filename": m.filename,
                "original_filename": m.original_filename,
                "url": m.url,
                "mime_type": m.mime_type,
                "file_size": m.file_size,
                "width": m.width,
                "height": m.height,
                "alt_text": m.alt_text,
                "caption": m.caption,
                "folder": m.folder,
                "uploaded_by": m.uploaded_by,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in items
        ],
        "total": total,
    }


@router.post("/folders")
async def create_folder(
    body: FolderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create folder (logical grouping). Folders are string values on Media records."""
    return {
        "message": "Folder created",
        "name": body.name,
        "parent_id": body.parent_id,
    }


@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    folder: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> dict:
    """Upload file (staff only). Creates Media record with file info, returns URL. Placeholder URL for now."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    content = await file.read()
    file_size = len(content)
    mime_type = file.content_type or "application/octet-stream"

    placeholder_url = f"/media/placeholder/{file.filename}"

    media = Media(
        filename=file.filename,
        original_filename=file.filename,
        url=placeholder_url,
        mime_type=mime_type,
        file_size=file_size,
        width=None,
        height=None,
        alt_text=None,
        caption=None,
        folder=folder,
        uploaded_by=current_user.id,
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)

    return {
        "id": media.id,
        "filename": media.filename,
        "url": media.url,
        "mime_type": media.mime_type,
        "file_size": media.file_size,
        "folder": media.folder,
    }


@router.get("/{media_id}")
async def get_media(
    media_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get media item by ID."""
    result = await db.execute(select(Media).where(Media.id == media_id))
    media = result.scalar_one_or_none()
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")

    return {
        "id": media.id,
        "filename": media.filename,
        "original_filename": media.original_filename,
        "url": media.url,
        "mime_type": media.mime_type,
        "file_size": media.file_size,
        "width": media.width,
        "height": media.height,
        "alt_text": media.alt_text,
        "caption": media.caption,
        "folder": media.folder,
        "uploaded_by": media.uploaded_by,
        "created_at": media.created_at.isoformat() if media.created_at else None,
    }


@router.delete("/{media_id}")
async def delete_media(
    media_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> dict:
    """Delete media (staff only)."""
    result = await db.execute(select(Media).where(Media.id == media_id))
    media = result.scalar_one_or_none()
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")

    await db.delete(media)
    await db.commit()
    return {"message": "Media deleted", "id": media_id}
