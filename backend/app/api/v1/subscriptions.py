"""Subscriptions API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...middleware.auth import get_current_user
from ...models.user import User
from ...services.commerce_service import SubscriptionService
from ...schemas.commerce import SubscriptionResponse

router = APIRouter()


def _subscription_to_response(sub) -> SubscriptionResponse:
    """Convert Subscription model to SubscriptionResponse."""
    return SubscriptionResponse(
        id=sub.id,
        user_id=sub.user_id,
        product_id=sub.product_id,
        status=sub.status.value if hasattr(sub.status, "value") else str(sub.status),
        current_period_start=sub.current_period_start,
        current_period_end=sub.current_period_end,
        cancel_at_period_end=sub.cancel_at_period_end,
        created_at=sub.created_at,
    )


@router.get("/", response_model=dict)
async def list_subscriptions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """List current user's subscriptions."""
    svc = SubscriptionService(db)
    items, total = await svc.list_subscriptions(user_id=user.id, skip=skip, limit=limit)
    return {
        "items": [_subscription_to_response(s) for s in items],
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    """Get subscription by ID."""
    svc = SubscriptionService(db)
    sub = await svc.get_subscription(subscription_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    if sub.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return _subscription_to_response(sub)


@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    """Cancel subscription."""
    svc = SubscriptionService(db)
    sub = await svc.cancel(subscription_id, user.id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return _subscription_to_response(sub)


@router.post("/{subscription_id}/pause", response_model=SubscriptionResponse)
async def pause_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    """Pause subscription."""
    svc = SubscriptionService(db)
    sub = await svc.pause(subscription_id, user.id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return _subscription_to_response(sub)


@router.post("/{subscription_id}/resume", response_model=SubscriptionResponse)
async def resume_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    """Resume paused subscription."""
    svc = SubscriptionService(db)
    sub = await svc.resume(subscription_id, user.id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return _subscription_to_response(sub)
