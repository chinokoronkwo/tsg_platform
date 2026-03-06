from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


class PageSectionCreate(BaseModel):
    block_type: str = Field(max_length=50)
    content: dict[str, Any] | None = None
    settings: dict[str, Any] | None = None
    sort_order: int = 0


class PageSectionResponse(BaseModel):
    id: int
    page_id: int
    block_type: str
    content: dict | None
    settings: dict | None
    sort_order: int

    model_config = {"from_attributes": True}


class PageCreate(BaseModel):
    title: str = Field(max_length=300)
    slug: str | None = None
    status: str = "draft"
    sections: list[PageSectionCreate] = []
    template: str | None = None
    parent_id: int | None = None


class PageUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    status: str | None = None
    sections: list[PageSectionCreate] | None = None
    template: str | None = None
    parent_id: int | None = None


class PageResponse(BaseModel):
    id: int
    title: str
    slug: str
    status: str
    template: str | None
    parent_id: int | None
    author_id: int
    sort_order: int
    published_at: datetime | None
    scheduled_at: datetime | None
    created_at: datetime
    updated_at: datetime
    sections: list[PageSectionResponse] = []

    model_config = {"from_attributes": True}


class PageRevisionResponse(BaseModel):
    id: int
    page_id: int
    revision_data: dict
    author_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PageListResponse(BaseModel):
    items: list[PageResponse]
    total: int
    page: int
    page_size: int


class MenuItemCreate(BaseModel):
    label: str = Field(max_length=200)
    url: str | None = None
    page_id: int | None = None
    target: str = "_self"
    css_class: str | None = None
    sort_order: int = 0
    children: list["MenuItemCreate"] = []


class MenuItemResponse(BaseModel):
    id: int
    menu_id: int
    parent_id: int | None
    label: str
    url: str | None
    page_id: int | None
    target: str
    css_class: str | None
    sort_order: int
    children: list["MenuItemResponse"] = []

    model_config = {"from_attributes": True}


MenuItemCreate.model_rebuild()
MenuItemResponse.model_rebuild()


class MenuCreate(BaseModel):
    name: str = Field(max_length=100)
    slug: str = Field(max_length=100)
    location: str | None = None
    items: list[MenuItemCreate] = []


class MenuResponse(BaseModel):
    id: int
    name: str
    slug: str
    location: str | None
    items: list[MenuItemResponse] = []

    model_config = {"from_attributes": True}


class MediaUploadResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    url: str
    mime_type: str
    file_size: int
    width: int | None
    height: int | None
    alt_text: str | None
    caption: str | None
    folder: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RedirectCreate(BaseModel):
    source_path: str = Field(max_length=500)
    target_path: str = Field(max_length=500)
    status_code: int = 301
    is_active: bool = True


class RedirectResponse(BaseModel):
    id: int
    source_path: str
    target_path: str
    status_code: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SEOMetadataCreate(BaseModel):
    title: str | None = None
    description: str | None = None
    canonical_url: str | None = None
    og_title: str | None = None
    og_description: str | None = None
    og_image: str | None = None
    json_ld: dict | None = None
    no_index: bool = False
    no_follow: bool = False


class SEOMetadataResponse(BaseModel):
    id: int
    page_id: int | None
    entity_type: str | None
    entity_id: int | None
    title: str | None
    description: str | None
    canonical_url: str | None
    og_title: str | None
    og_description: str | None
    og_image: str | None
    json_ld: dict | None = None
    no_index: bool
    no_follow: bool

    model_config = {"from_attributes": True}
