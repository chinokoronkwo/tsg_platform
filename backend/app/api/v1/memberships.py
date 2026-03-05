"""Memberships API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...core.database import get_db
from ...middleware.auth import get_current_user, require_admin
from ...models.user import User
from ...models.commerce import Membership
from ...services.commerce_service import MembershipService
from ...schemas.commerce import (
    MembershipPlanCreate,
    MembershipPlanResponse,
    MembershipResponse,
    AssignMembershipRequest,
)

router = APIRouter()


def _plan_to_response(plan) -> MembershipPlanResponse:
    """Convert MembershipPlan model to MembershipPlanResponse."""
    return MembershipPlanResponse(
        id=plan.id,
        name=plan.name,
        slug=plan.slug,
        tier=plan.tier.value if hasattr(plan.tier, "value") else str(plan.tier),
        price=plan.price,
        description=plan.description,
        features_json=plan.features_json,
        is_active=plan.is_active,
    )


def _membership_to_response(membership) -> MembershipResponse:
    """Convert Membership model to MembershipResponse."""
    plan_data = None
    if membership.plan:
        plan_data = _plan_to_response(membership.plan)
    return MembershipResponse(
        id=membership.id,
        user_id=membership.user_id,
        plan_id=membership.plan_id,
        status=membership.status,
        starts_at=membership.starts_at,
        expires_at=membership.expires_at,
        plan=plan_data,
    )


@router.get("/plans", response_model=dict)
async def list_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all membership plans."""
    svc = MembershipService(db)
    plans = await svc.list_plans()
    total = len(plans)
    items = plans[skip : skip + limit]
    return {
        "items": [_plan_to_response(p) for p in items],
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.get("/plans/{plan_id}", response_model=MembershipPlanResponse)
async def get_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
) -> MembershipPlanResponse:
    """Get membership plan by ID."""
    svc = MembershipService(db)
    plan = await svc.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return _plan_to_response(plan)


@router.post("/plans", response_model=MembershipPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    data: MembershipPlanCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> MembershipPlanResponse:
    """Create membership plan (admin only)."""
    svc = MembershipService(db)
    try:
        plan = await svc.create_plan(data)
        return _plan_to_response(plan)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/my", response_model=dict)
async def list_my_memberships(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """List current user's memberships."""
    svc = MembershipService(db)
    memberships = await svc.get_user_memberships(user.id)
    total = len(memberships)
    items = memberships[skip : skip + limit]
    return {
        "items": [_membership_to_response(m) for m in items],
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.post("/assign", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
async def assign_membership(
    data: AssignMembershipRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> MembershipResponse:
    """Assign membership plan to user (admin only)."""
    svc = MembershipService(db)
    try:
        membership = await svc.assign_membership(data.user_id, data.plan_id)
        result = await db.execute(
            select(Membership)
            .options(selectinload(Membership.plan))
            .where(Membership.id == membership.id)
        )
        m = result.scalar_one()
        return _membership_to_response(m)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))