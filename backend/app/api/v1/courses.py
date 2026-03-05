"""Courses API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...middleware.auth import get_current_user, require_admin, require_staff
from ...models.user import User
from ...models.lms import CourseStatus
from ...services.lms_service import CourseService
from ...schemas.lms import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseListResponse,
    ModuleResponse,
)

router = APIRouter()


@router.get("/", response_model=CourseListResponse)
async def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: CourseStatus | None = None,
    tier: str | None = Query(None, alias="min_membership_tier"),
    search: str | None = None,
    instructor_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List courses with filters and pagination."""
    service = CourseService(db)
    courses, total = await service.list_courses(
        skip=skip,
        limit=limit,
        status=status,
        min_membership_tier=tier,
        search=search,
        instructor_id=instructor_id,
    )
    page = (skip // limit) + 1 if limit > 0 else 1
    return CourseListResponse(
        items=[CourseResponse.model_validate(c) for c in courses],
        total=total,
        page=page,
        page_size=limit,
    )


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get course by ID with modules and lessons."""
    service = CourseService(db)
    course = await service.get_course(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    return CourseResponse.model_validate(course)


@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_staff),
):
    """Create a new course (staff only)."""
    service = CourseService(db)
    course = await service.create_course(data)
    return CourseResponse.model_validate(course)


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_staff),
):
    """Update course details (staff only)."""
    service = CourseService(db)
    course = await service.update_course(course_id, data)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    return CourseResponse.model_validate(course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """Delete course (admin only)."""
    service = CourseService(db)
    deleted = await service.delete_course(course_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )


@router.get("/{course_id}/modules", response_model=list[ModuleResponse])
async def list_modules(
    course_id: int,
    db: AsyncSession = Depends(get_db),
):
    """List modules in a course."""
    service = CourseService(db)
    course = await service.get_course(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    return [ModuleResponse.model_validate(m) for m in course.modules]
