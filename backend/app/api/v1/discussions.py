"""Discussions API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...middleware.auth import get_current_user, require_staff
from ...models.user import User
from ...services.lms_service import DiscussionService
from ...schemas.lms import (
    DiscussionThreadCreate,
    DiscussionThreadResponse,
    DiscussionThreadDetailResponse,
    DiscussionPostCreate,
    DiscussionPostResponse,
)

router = APIRouter()


@router.get("/", response_model=list[DiscussionThreadResponse])
async def list_threads(
    course_id: int = Query(..., description="Filter by course ID"),
    lesson_id: int | None = Query(None, description="Filter by lesson ID"),
    db: AsyncSession = Depends(get_db),
):
    """List discussion threads, optionally filtered by course_id and lesson_id."""
    service = DiscussionService(db)
    threads = await service.list_threads(course_id=course_id, lesson_id=lesson_id)
    return [DiscussionThreadResponse.model_validate(t) for t in threads]


@router.get("/{thread_id}", response_model=DiscussionThreadDetailResponse)
async def get_thread(
    thread_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get thread by ID with posts."""
    service = DiscussionService(db)
    thread = await service.get_thread(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )
    return DiscussionThreadDetailResponse.model_validate(thread)


@router.post("/", response_model=DiscussionThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    data: DiscussionThreadCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new discussion thread."""
    service = DiscussionService(db)
    thread = await service.create_thread(user.id, data)
    return DiscussionThreadResponse.model_validate(thread)


@router.post("/{thread_id}/posts", response_model=DiscussionPostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    thread_id: int,
    data: DiscussionPostCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create post/reply in thread."""
    service = DiscussionService(db)
    try:
        post = await service.create_post(thread_id, user.id, data)
        return DiscussionPostResponse.model_validate(post)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/{thread_id}/pin", response_model=DiscussionThreadResponse)
async def toggle_pin(
    thread_id: int,
    pinned: bool | None = Query(None, description="Set pin state; omit to toggle"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_staff),
):
    """Toggle or set pin state (staff only)."""
    service = DiscussionService(db)
    thread = await service.get_thread(thread_id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )
    if pinned is None:
        pinned = not thread.is_pinned
    updated = await service.pin_thread(thread_id, pinned=pinned)
    return DiscussionThreadResponse.model_validate(updated)
