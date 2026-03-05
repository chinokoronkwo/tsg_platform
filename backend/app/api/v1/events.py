"""Events API endpoints. Uses Product model with type=event and EventDetail."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from ...core.database import get_db
from ...middleware.auth import get_current_user, require_admin
from ...models.user import User
from ...services.event_service import EventService
from ...schemas.events import (
    EventResponse,
    EventListResponse,
    EventCalendarResponse,
    RSVPRequest,
    AttendeeResponse,
)

router = APIRouter()


@router.get("/", response_model=EventListResponse)
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> EventListResponse:
    """List events (products where type=event, with event_detail loaded)."""
    svc = EventService(db)
    items, total = await svc.list_events(
        start_date=from_date,
        end_date=to_date,
        search=search,
        skip=skip,
        limit=limit,
    )
    return EventListResponse(
        items=items,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.get("/calendar", response_model=list)
async def calendar_view(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Calendar view - events grouped by month/week."""
    svc = EventService(db)
    return await svc.calendar_view(year=year, month=month)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    """Get event detail."""
    svc = EventService(db)
    event = await svc.get_event(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.post("/{event_id}/rsvp", status_code=status.HTTP_201_CREATED)
async def rsvp_event(
    event_id: int,
    data: RSVPRequest | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """RSVP to event (create EventAttendee)."""
    svc = EventService(db)
    try:
        ticket_id = data.ticket_id if data else None
        attendee = await svc.rsvp(event_id, user_id=user.id, ticket_id=ticket_id)
        return {"message": "RSVP successful", "attendee_id": attendee.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{event_id}/attendees", response_model=dict)
async def list_attendees(
    event_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    """List attendees (admin only)."""
    svc = EventService(db)
    items, total = await svc.list_attendees(event_id, skip=skip, limit=limit)
    return {
        "items": [
            AttendeeResponse(
                id=a.id,
                user_id=a.user_id,
                event_id=a.event_id,
                status=a.status,
                checked_in=a.checked_in,
                checked_in_at=a.checked_in_at,
                created_at=a.created_at,
                email=a.user.email if a.user else None,
                first_name=a.user.first_name if a.user else None,
                last_name=a.user.last_name if a.user else None,
                display_name=a.user.display_name if a.user else None,
            )
            for a in items
        ],
        "total": total,
    }


@router.patch("/{event_id}/attendees/{attendee_id}/check-in")
async def check_in_attendee(
    event_id: int,
    attendee_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict:
    """Check in attendee (admin only)."""
    from sqlalchemy import select
    from ...models.commerce import Product, EventDetail, EventAttendee, ProductType

    svc = EventService(db)
    ev = await svc.get_event(event_id)
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    result = await db.execute(
        select(EventDetail).join(Product).where(
            Product.id == event_id,
            Product.product_type == ProductType.EVENT,
        )
    )
    ed = result.scalar_one_or_none()
    if not ed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    attendee_result = await db.execute(
        select(EventAttendee).where(
            EventAttendee.id == attendee_id,
            EventAttendee.event_id == ed.id,
        )
    )
    attendee = attendee_result.scalar_one_or_none()
    if not attendee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendee not found")
    attendee = await svc.check_in(attendee_id)
    return {"message": "Checked in", "attendee_id": attendee.id}
