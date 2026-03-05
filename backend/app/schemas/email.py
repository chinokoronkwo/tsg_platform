"""Email schemas for Snob Group platform."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EmailListCreate(BaseModel):
    name: str = Field(max_length=200)
    description: str | None = None
    is_dynamic: bool = False
    filter_criteria: dict[str, Any] | None = None


class EmailListResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_dynamic: bool
    filter_criteria: dict[str, Any] | None
    subscriber_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailSubscriberCreate(BaseModel):
    email: str = Field(max_length=255)
    first_name: str | None = None
    last_name: str | None = None
    status: str = "subscribed"


class EmailSubscriberResponse(BaseModel):
    id: int
    list_id: int
    email: str
    first_name: str | None
    last_name: str | None
    status: str
    subscribed_at: datetime

    model_config = {"from_attributes": True}


class EmailTemplateCreate(BaseModel):
    name: str = Field(max_length=200)
    subject: str = Field(max_length=300)
    body_html: str
    body_text: str | None = None
    category: str | None = None
    variables: list[str] | dict[str, Any] | None = None


class EmailTemplateUpdate(BaseModel):
    name: str | None = None
    subject: str | None = None
    body_html: str | None = None
    body_text: str | None = None
    category: str | None = None
    variables: list[str] | dict[str, Any] | None = None


class EmailTemplateResponse(BaseModel):
    id: int
    name: str
    subject: str
    body_html: str
    body_text: str | None
    category: str | None
    variables: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmailCampaignStats(BaseModel):
    sent_count: int = 0
    open_count: int = 0
    click_count: int = 0


class EmailCampaignCreate(BaseModel):
    name: str = Field(max_length=200)
    subject: str = Field(max_length=300)
    template_id: int | None = None
    list_ids: list[int] = Field(default_factory=list)
    status: str = "draft"
    scheduled_at: datetime | None = None


class EmailCampaignResponse(BaseModel):
    id: int
    name: str
    subject: str
    template_id: int | None
    list_ids: list[int] | None
    status: str
    scheduled_at: datetime | None
    sent_at: datetime | None
    stats: EmailCampaignStats
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailCampaignListResponse(BaseModel):
    items: list[EmailCampaignResponse]
    total: int
    page: int
    page_size: int
