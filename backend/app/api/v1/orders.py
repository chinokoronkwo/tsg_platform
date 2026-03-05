"""Orders API endpoints."""

from fastapi import APIRouter, Body, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ...core.database import get_db
from ...middleware.auth import get_current_user, require_admin
from ...models.user import User
from ...services.commerce_service import OrderService
from ...schemas.commerce import CheckoutRequest, OrderResponse, OrderStatusUpdate, RefundRequest

router = APIRouter()


def _order_to_response(order) -> OrderResponse:
    """Convert Order model to OrderResponse."""
    items = [
        {
            "id": item.id,
            "product_id": item.product_id,
            "name": item.name,
            "sku": item.sku,
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "total": float(item.total),
        }
        for item in order.items
    ]
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status.value if hasattr(order.status, "value") else str(order.status),
        subtotal=order.subtotal,
        tax_total=order.tax_total,
        discount_total=order.discount_total,
        fee_total=order.fee_total,
        total=order.total,
        items=items,
        created_at=order.created_at,
    )


@router.get("/", response_model=dict)
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """List orders. Users see their own; admins see all."""
    svc = OrderService(db)
    is_admin = user.is_superuser or any(r.slug == "administrator" for r in user.roles)
    user_id = None if is_admin else user.id
    orders, total = await svc.list_orders(
        user_id=user_id,
        skip=skip,
        limit=limit,
        status=status,
    )
    return {
        "items": [_order_to_response(o) for o in orders],
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderResponse:
    """Get order by ID."""
    svc = OrderService(db)
    order = await svc.get_order(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    is_admin = user.is_superuser or any(r.slug == "administrator" for r in user.roles)
    if not is_admin and order.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return _order_to_response(order)


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderResponse:
    """Create order (checkout)."""
    svc = OrderService(db)
    try:
        order = await svc.create_order(user.id, data)
        return _order_to_response(order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> OrderResponse:
    """Update order status (admin only)."""
    svc = OrderService(db)
    order = await svc.update_status(order_id, data.status)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return _order_to_response(order)


@router.post("/{order_id}/refund", response_model=OrderResponse)
async def refund_order(
    order_id: int,
    data: RefundRequest = Body(default=RefundRequest()),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> OrderResponse:
    """Refund order (admin only)."""
    svc = OrderService(db)
    amount = data.amount
    try:
        order = await svc.refund_order(order_id, amount=amount)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return _order_to_response(order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
