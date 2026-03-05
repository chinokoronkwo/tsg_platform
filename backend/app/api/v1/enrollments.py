"""Enrollments API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...middleware.auth import get_current_user
from ...models.user import User
from ...services.lms_service import EnrollmentService
from ...schemas.lms import (
    EnrollRequest,
    EnrollmentResponse,
    CourseProgressUpdate,
)

router = APIRouter()


@router.get("/", response_model=list[EnrollmentResponse])
async def list_enrollments(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List current user's enrollments."""
    service = EnrollmentService(db)
    enrollments = await service.get_user_enrollments(user.id)
    return [EnrollmentResponse.model_validate(e) for e in enrollments]


@router.post("/", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll(
    data: EnrollRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Enroll current user in a course."""
    service = EnrollmentService(db)
    try:
        enrollment = await service.enroll_user(user.id, data.course_id)
        return EnrollmentResponse.model_validate(enrollment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{enrollment_id}", response_model=EnrollmentResponse)
async def get_enrollment(
    enrollment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get enrollment with progress (own enrollments only)."""
    service = EnrollmentService(db)
    enrollment = await service.get_enrollment_by_id(enrollment_id, user_id=user.id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found",
        )
    return EnrollmentResponse.model_validate(enrollment)


@router.put("/{enrollment_id}/progress", response_model=EnrollmentResponse)
async def update_progress(
    enrollment_id: int,
    data: CourseProgressUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update progress (mark lesson complete, time spent)."""
    service = EnrollmentService(db)
    enrollment = await service.get_enrollment_by_id(enrollment_id, user_id=user.id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found",
        )

    updated = await service.update_progress(user.id, enrollment.course_id, data)
    return EnrollmentResponse.model_validate(updated)
