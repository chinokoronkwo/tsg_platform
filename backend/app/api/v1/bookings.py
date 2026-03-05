"""Bookings API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from ...core.database import get_db
from ...middleware.auth import get_current_user, require_admin
from ...models.user import User
from ...services.booking_service import BookingService
from ...schemas.booking import (
    BookingResourceCreate,
    BookingResourceResponse,
    BookingSlotCreate,
    BookingSlotResponse,
    BookingCreate,
    BookingResponse,
    BookingListResponse,
    UserInfo,
)

router = APIRouter()


def _booking_to_response(booking) -> BookingResponse:
    user_info = UserInfo(
        id=booking.user.id,
        email=booking.user.email,
        first_name=booking.user.first_name or "",
        last_name=booking.user.last_name or "",
        display_name=booking.user.display_name or "",
    ) if booking.user else None
    slot_resp = (
        BookingSlotResponse(
            id=booking.slot.id,
            resource_id=booking.slot.resource_id,
            start_time=booking.slot.start_time,
            end_time=booking.slot.end_time,
            capacity=booking.slot.capacity,
            booked_count=booking.slot.booked_count,
            is_available=booking.slot.is_available,
        )
        if booking.slot
        else None
    )
    return BookingResponse(
        id=booking.id,
        slot_id=booking.slot_id,
        user_id=booking.user_id,
        notes=booking.notes,
        status=booking.status.value if hasattr(booking.status, "value") else str(booking.status),
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        user=user_info,
        slot=slot_resp,
    )


# --- Resources ---
@router.get("/resources", response_model=dict)
async def list_resources(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List booking resources."""
    svc = BookingService(db)
    items, total = await svc.list_resources(skip=skip, limit=limit, is_active=is_active)
    return {
        "items": [
            BookingResourceResponse.model_validate(r) for r in items
        ],
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.post("/resources", response_model=BookingResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    data: BookingResourceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> BookingResourceResponse:
    """Create a booking resource (admin only)."""
    svc = BookingService(db)
    resource = await svc.create_resource(data)
    return BookingResourceResponse.model_validate(resource)


@router.get("/resources/{resource_id}/slots", response_model=dict)
async def list_resource_slots(
    resource_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List available slots for a resource with optional date filters."""
    svc = BookingService(db)
    resource = await svc.get_resource(resource_id)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    items, total = await svc.list_slots(
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return {
        "items": [BookingSlotResponse.model_validate(s) for s in items],
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.post("/slots", response_model=BookingSlotResponse, status_code=status.HTTP_201_CREATED)
async def create_slot(
    data: BookingSlotCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> BookingSlotResponse:
    """Create a booking slot (admin only)."""
    svc = BookingService(db)
    resource = await svc.get_resource(data.resource_id)
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    slot = await svc.create_slot(data)
    return BookingSlotResponse.model_validate(slot)


# --- Bookings ---
@router.get("/", response_model=BookingListResponse)
async def list_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingListResponse:
    """List bookings (user's own, or all for admin)."""
    svc = BookingService(db)
    # Check if admin - use optional to avoid requiring admin for all users
    is_admin = user.is_superuser or any(r.slug == "administrator" for r in user.roles)
    user_id = None if is_admin else user.id
    items, total = await svc.list_bookings(user_id=user_id, skip=skip, limit=limit)
    return BookingListResponse(
        items=[_booking_to_response(b) for b in items],
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingResponse:
    """Get booking by ID."""
    svc = BookingService(db)
    is_admin = user.is_superuser or any(r.slug == "administrator" for r in user.roles)
    user_id = None if is_admin else user.id
    booking = await svc.get_booking(booking_id, user_id=user_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return _booking_to_response(booking)


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingResponse:
    """Create a booking (authenticated)."""
    svc = BookingService(db)
    try:
        booking = await svc.create_booking(data, user_id=user.id)
        # Reload with relations for response
        booking = await svc.get_booking(booking.id, user_id=None)
        return _booking_to_response(booking)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingResponse:
    """Cancel a booking."""
    svc = BookingService(db)
    is_admin = user.is_superuser or any(r.slug == "administrator" for r in user.roles)
    user_id = None if is_admin else user.id
    booking = await svc.cancel_booking(booking_id, user_id=user_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    booking = await svc.get_booking(booking.id, user_id=user_id)
    return _booking_to_response(booking)
