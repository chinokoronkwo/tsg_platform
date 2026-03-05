from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class EventResponse(BaseModel):
    """Product info + event_detail fields."""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    status: str
    price: Decimal
    sale_price: Optional[Decimal] = None
    # Event detail fields
    start: datetime
    end: Optional[datetime] = None
    venue: Optional[str] = None
    venue_address: Optional[str] = None
    capacity: Optional[int] = None
    attendee_count: int = 0
    rsvp_enabled: bool = False
    timezone: str = "America/New_York"
    created_at: datetime

    model_config = {"from_attributes": True}


class EventCalendarResponse(BaseModel):
    """Events grouped by date."""
    date: str  # YYYY-MM-DD
    events: list[EventResponse]


class RSVPRequest(BaseModel):
    ticket_id: Optional[int] = None
    status: str = "registered"


class AttendeeResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    status: str
    checked_in: bool
    checked_in_at: Optional[datetime] = None
    created_at: datetime
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    items: list[EventResponse]
    total: int
    page: int
    page_size: int
