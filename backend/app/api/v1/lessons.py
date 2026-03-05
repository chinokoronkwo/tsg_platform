"""Lessons API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ...core.database import get_db
from ...middleware.auth import get_current_user, require_staff
from ...models.user import User
from ...models.lms import Lesson, Module
from ...services.lms_service import LessonService, EnrollmentService
from ...schemas.lms import (
    LessonCreate,
    LessonCreateInModule,
    LessonUpdate,
    LessonResponse,
    CourseProgressUpdate,
    EnrollmentResponse,
)

router = APIRouter()


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get lesson by ID with content."""
    service = LessonService(db)
    lesson = await service.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )
    return LessonResponse.model_validate(lesson)


@router.post("/", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    data: LessonCreateInModule,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_staff),
):
    """Create a new lesson in a module (staff only)."""
    service = LessonService(db)
    lesson_create = LessonCreate(**data.model_dump(exclude={"module_id"}))
    lesson = await service.create_lesson(data.module_id, lesson_create)
    return LessonResponse.model_validate(lesson)


@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: int,
    data: LessonUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_staff),
):
    """Update lesson details (staff only)."""
    service = LessonService(db)
    lesson = await service.update_lesson(lesson_id, data)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )
    return LessonResponse.model_validate(lesson)


@router.post("/{lesson_id}/complete", response_model=EnrollmentResponse)
async def mark_lesson_complete(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Mark lesson as complete for current user."""
    result = await db.execute(
        select(Lesson)
        .options(selectinload(Lesson.module))
        .where(Lesson.id == lesson_id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    course_id = lesson.module.course_id
    enrollment_service = EnrollmentService(db)
    enrollment = await enrollment_service.get_enrollment(user.id, course_id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not enrolled in this course",
        )

    enrollment = await enrollment_service.update_progress(
        user.id,
        course_id,
        CourseProgressUpdate(lesson_id=lesson_id, is_completed=True, time_spent_seconds=0),
    )
    return EnrollmentResponse.model_validate(enrollment)
