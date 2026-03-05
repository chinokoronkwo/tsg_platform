"""SMS schemas for Snob Group platform."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SMSContactCreate(BaseModel):
    phone_number: str = Field(max_length=20)
    first_name: str | None = None
    last_name: str | None = None
    tags: list[str] | None = None
    custom_fields: dict[str, Any] | None = None
    is_opted_in: bool = True


class SMSContactResponse(BaseModel):
    id: int
    phone_number: str
    first_name: str | None
    last_name: str | None
    tags: list[str] | None
    custom_fields: dict[str, Any] | None
    is_opted_in: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SMSContactListCreate(BaseModel):
    name: str = Field(max_length=200)
    description: str | None = None
    is_dynamic: bool = False
    filter_criteria: dict[str, Any] | None = None


class SMSContactListResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_dynamic: bool
    filter_criteria: dict[str, Any] | None
    member_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SMSTemplateCreate(BaseModel):
    name: str = Field(max_length=200)
    body: str
    category: str | None = None
    merge_fields: list[str] | dict[str, Any] | None = None


class SMSTemplateUpdate(BaseModel):
    name: str | None = None
    body: str | None = None
    category: str | None = None
    merge_fields: list[str] | dict[str, Any] | None = None


class SMSTemplateResponse(BaseModel):
    id: int
    name: str
    body: str
    category: str | None
    merge_fields: dict[str, Any] | None
    character_count: int | None
    segment_count: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SMSCampaignStats(BaseModel):
    sent: int = 0
    delivered: int = 0
    failed: int = 0
    opt_out: int = 0


class SMSCampaignCreate(BaseModel):
    name: str = Field(max_length=200)
    template_id: int | None = None
    body: str | None = None
    list_ids: list[int] = Field(default_factory=list)
    status: str = "draft"
    scheduled_at: datetime | None = None


class SMSCampaignResponse(BaseModel):
    id: int
    name: str
    template_id: int | None
    body: str | None
    list_ids: list[int] | None
    status: str
    scheduled_at: datetime | None
    sent_at: datetime | None
    stats: SMSCampaignStats
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SMSCampaignListResponse(BaseModel):
    items: list[SMSCampaignResponse]
    total: int
    page: int
    page_size: int


class ImportContactItem(BaseModel):
    phone_number: str = Field(max_length=20)
    first_name: str | None = None
    last_name: str | None = None


class ImportContactsRequest(BaseModel):
    contacts: list[ImportContactItem]


class DeliveryStatsResponse(BaseModel):
    total: int = 0
    sent: int = 0
    delivered: int = 0
    failed: int = 0
    bounced: int = 0
    opt_out: int = 0


class AddMembersRequest(BaseModel):
    contact_ids: list[int]


class OptOutRequest(BaseModel):
    phone: str = Field(max_length=20)
    reason: str | None = None
