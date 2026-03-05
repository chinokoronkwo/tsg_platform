from datetime import date, datetime
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.commerce import (
    Product,
    ProductType,
    EventDetail,
    EventAttendee,
)
from ..schemas.events import EventResponse


class EventService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _product_to_event_response(self, product: Product) -> EventResponse:
        ed = product.event_detail
        if not ed:
            raise ValueError("Product has no event detail")
        attendee_count = len(ed.attendees) if ed.attendees else 0
        return EventResponse(
            id=product.id,
            name=product.name,
            slug=product.slug,
            description=product.description,
            short_description=product.short_description,
            status=product.status.value if hasattr(product.status, "value") else str(product.status),
            price=product.price,
            sale_price=product.sale_price,
            start=ed.event_start if ed else None,
            end=ed.event_end if ed else None,
            venue=ed.venue_name if ed else None,
            venue_address=ed.venue_address if ed else None,
            capacity=ed.capacity if ed else None,
            attendee_count=attendee_count,
            rsvp_enabled=ed.rsvp_enabled if ed else False,
            timezone=ed.timezone if ed else "America/New_York",
            created_at=product.created_at,
        )

    async def list_events(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[EventResponse], int]:
        query = (
            select(Product)
            .join(EventDetail, Product.id == EventDetail.product_id, isouter=False)
            .where(Product.product_type == ProductType.EVENT)
        )
        if start_date is not None:
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.where(EventDetail.event_start >= start_dt)
        if end_date is not None:
            from datetime import time
            end_dt = datetime.combine(end_date, time(23, 59, 59, 999999))
            query = query.where(EventDetail.event_start <= end_dt)
        if search:
            query = query.where(Product.name.ilike(f"%{search}%"))
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = (
            query.options(selectinload(Product.event_detail).selectinload(EventDetail.attendees))
            .offset(skip)
            .limit(limit)
            .order_by(EventDetail.event_start)
        )
        result = await self.db.execute(query)
        products = result.scalars().unique().all()
        items = [self._product_to_event_response(p) for p in products]
        return items, total

    async def get_event(self, event_id: int) -> EventResponse | None:
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.event_detail).selectinload(EventDetail.attendees),
                selectinload(Product.event_detail).selectinload(EventDetail.tickets),
            )
            .where(Product.id == event_id)
            .where(Product.product_type == ProductType.EVENT)
        )
        product = result.scalar_one_or_none()
        if not product:
            return None
        return self._product_to_event_response(product)

    async def calendar_view(self, year: int, month: int) -> list[dict]:
        """Group events by date for calendar view."""
        from calendar import monthrange
        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)
        items, _ = await self.list_events(start_date=start_date, end_date=end_date, limit=500)
        grouped: dict[str, list[EventResponse]] = defaultdict(list)
        for ev in items:
            d = ev.start.date() if hasattr(ev.start, "date") else ev.start
            key = d.isoformat() if hasattr(d, "isoformat") else str(d)
            grouped[key].append(ev)
        return [{"date": k, "events": v} for k, v in sorted(grouped.items())]

    async def rsvp(self, event_id: int, user_id: int, ticket_id: int | None = None) -> EventAttendee:
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.event_detail).selectinload(EventDetail.attendees))
            .where(Product.id == event_id)
            .where(Product.product_type == ProductType.EVENT)
        )
        product = result.scalar_one_or_none()
        if not product or not product.event_detail:
            raise ValueError("Event not found")
        ed = product.event_detail
        if not ed.rsvp_enabled:
            raise ValueError("RSVP is not enabled for this event")
        if ed.capacity is not None:
            current_count = len(ed.attendees)
            if current_count >= ed.capacity:
                raise ValueError("Event is at capacity")
        existing = next((a for a in ed.attendees if a.user_id == user_id), None)
        if existing:
            raise ValueError("Already registered for this event")
        attendee = EventAttendee(
            event_id=ed.id,
            user_id=user_id,
            ticket_id=ticket_id,
            status="registered",
        )
        self.db.add(attendee)
        await self.db.commit()
        await self.db.refresh(attendee)
        return attendee

    async def list_attendees(
        self,
        event_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[EventAttendee], int]:
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.event_detail))
            .where(Product.id == event_id)
            .where(Product.product_type == ProductType.EVENT)
        )
        product = result.scalar_one_or_none()
        if not product or not product.event_detail:
            return [], 0
        ed = product.event_detail
        query = (
            select(EventAttendee)
            .options(selectinload(EventAttendee.user))
            .where(EventAttendee.event_id == ed.id)
        )
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset(skip).limit(limit).order_by(EventAttendee.created_at)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def check_in(self, attendee_id: int) -> EventAttendee | None:
        from datetime import timezone
        result = await self.db.execute(
            select(EventAttendee).where(EventAttendee.id == attendee_id)
        )
        attendee = result.scalar_one_or_none()
        if not attendee:
            return None
        attendee.checked_in = True
        attendee.checked_in_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(attendee)
        return attendee
