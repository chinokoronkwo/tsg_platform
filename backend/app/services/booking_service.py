from datetime import date, datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.booking import BookingResource, BookingSlot, Booking, BookingStatus
from ..schemas.booking import (
    BookingResourceCreate,
    BookingSlotCreate,
    BookingCreate,
)


class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_resources(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: bool | None = None,
    ) -> tuple[list[BookingResource], int]:
        query = select(BookingResource)
        if is_active is not None:
            query = query.where(BookingResource.is_active == is_active)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset(skip).limit(limit).order_by(BookingResource.name)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_resource(self, resource_id: int) -> BookingResource | None:
        result = await self.db.execute(
            select(BookingResource).where(BookingResource.id == resource_id)
        )
        return result.scalar_one_or_none()

    async def create_resource(self, data: BookingResourceCreate) -> BookingResource:
        resource = BookingResource(
            name=data.name,
            description=data.description,
            resource_type=data.resource_type,
            is_active=data.is_active,
        )
        self.db.add(resource)
        await self.db.commit()
        await self.db.refresh(resource)
        return resource

    async def list_slots(
        self,
        resource_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[BookingSlot], int]:
        query = select(BookingSlot).where(BookingSlot.resource_id == resource_id)
        if start_date is not None:
            query = query.where(BookingSlot.start_time >= datetime.combine(start_date, datetime.min.time()))
        if end_date is not None:
            query = query.where(BookingSlot.end_time <= datetime.combine(end_date, datetime.max.time()))
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset(skip).limit(limit).order_by(BookingSlot.start_time)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def create_slot(self, data: BookingSlotCreate) -> BookingSlot:
        slot = BookingSlot(
            resource_id=data.resource_id,
            start_time=data.start_time,
            end_time=data.end_time,
            capacity=data.capacity,
            is_available=data.is_available,
        )
        self.db.add(slot)
        await self.db.commit()
        await self.db.refresh(slot)
        return slot

    async def list_bookings(
        self,
        user_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Booking], int]:
        query = select(Booking)
        if user_id is not None:
            query = query.where(Booking.user_id == user_id)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = (
            query.options(
                selectinload(Booking.user),
                selectinload(Booking.slot).selectinload(BookingSlot.resource),
            )
            .offset(skip)
            .limit(limit)
            .order_by(Booking.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def list_user_bookings(self, user_id: int, skip: int = 0, limit: int = 20) -> tuple[list[Booking], int]:
        return await self.list_bookings(user_id=user_id, skip=skip, limit=limit)

    async def create_booking(self, data: BookingCreate, user_id: int) -> Booking:
        result = await self.db.execute(
            select(BookingSlot)
            .where(BookingSlot.id == data.slot_id)
            .with_for_update()
        )
        slot = result.scalar_one_or_none()
        if not slot:
            raise ValueError("Slot not found")
        if not slot.is_available:
            raise ValueError("Slot is not available for booking")
        if slot.booked_count >= slot.capacity:
            raise ValueError("Slot is at capacity")
        status = BookingStatus(data.status) if data.status else BookingStatus.PENDING
        booking = Booking(
            slot_id=data.slot_id,
            user_id=user_id,
            notes=data.notes,
            status=status,
        )
        slot.booked_count += 1
        self.db.add(booking)
        await self.db.commit()
        await self.db.refresh(booking)
        await self.db.refresh(slot)
        return booking

    async def cancel_booking(self, booking_id: int, user_id: int | None = None) -> Booking | None:
        result = await self.db.execute(
            select(Booking)
            .options(selectinload(Booking.slot))
            .where(Booking.id == booking_id)
            .with_for_update()
        )
        booking = result.scalar_one_or_none()
        if not booking:
            return None
        if user_id is not None and booking.user_id != user_id:
            return None
        if booking.status == BookingStatus.CANCELLED:
            return booking
        booking.status = BookingStatus.CANCELLED
        booking.slot.booked_count = max(0, booking.slot.booked_count - 1)
        await self.db.commit()
        await self.db.refresh(booking)
        return booking

    async def get_booking(
        self,
        booking_id: int,
        user_id: int | None = None,
    ) -> Booking | None:
        query = (
            select(Booking)
            .options(
                selectinload(Booking.user),
                selectinload(Booking.slot).selectinload(BookingSlot.resource),
            )
            .where(Booking.id == booking_id)
        )
        if user_id is not None:
            query = query.where(Booking.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
