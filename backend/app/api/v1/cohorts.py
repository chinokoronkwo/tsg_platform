"""Cohorts API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...middleware.auth import get_current_user, require_staff
from ...models.user import User
from ...services.lms_service import CohortService
from ...schemas.lms import (
    CohortCreate,
    CohortResponse,
    CohortDetailResponse,
    CohortAddMemberRequest,
)

router = APIRouter()


@router.get("/", response_model=list[CohortResponse])
async def list_cohorts(
    course_id: int | None = Query(None, description="Filter by course ID"),
    db: AsyncSession = Depends(get_db),
):
    """List cohorts, optionally filtered by course_id."""
    service = CohortService(db)
    cohorts = await service.list_cohorts(course_id=course_id)
    return [CohortResponse.model_validate(c) for c in cohorts]


@router.get("/{cohort_id}", response_model=CohortDetailResponse)
async def get_cohort(
    cohort_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get cohort by ID with members."""
    service = CohortService(db)
    cohort = await service.get_cohort(cohort_id)
    if not cohort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cohort not found",
        )
    return CohortDetailResponse.model_validate(cohort)


@router.post("/", response_model=CohortResponse, status_code=status.HTTP_201_CREATED)
async def create_cohort(
    data: CohortCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_staff),
):
    """Create a new cohort (staff only)."""
    service = CohortService(db)
    cohort = await service.create_cohort(data)
    return CohortResponse.model_validate(cohort)


@router.post("/{cohort_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    cohort_id: int,
    data: CohortAddMemberRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_staff),
):
    """Add member to cohort."""
    service = CohortService(db)
    try:
        member = await service.add_member(cohort_id, data.user_id)
        return {"id": member.id, "user_id": member.user_id, "cohort_id": member.cohort_id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{cohort_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    cohort_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_staff),
):
    """Remove member from cohort."""
    service = CohortService(db)
    removed = await service.remove_member(cohort_id, user_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in cohort",
        )
