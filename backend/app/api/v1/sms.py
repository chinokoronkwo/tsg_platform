"""SMS API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...middleware.auth import get_current_user, require_admin, require_staff
from ...models.user import User
from ...services.sms_service import (
    SMSContactService,
    SMSListService,
    SMSTemplateService,
    SMSCampaignService,
    OptOutService,
    SMSSendService,
)
from ...schemas.sms import (
    SMSContactCreate,
    SMSContactResponse,
    SMSContactListCreate,
    SMSContactListResponse,
    SMSTemplateCreate,
    SMSTemplateUpdate,
    SMSTemplateResponse,
    SMSCampaignCreate,
    SMSCampaignResponse,
    SMSCampaignListResponse,
    SMSCampaignStats,
    ImportContactsRequest,
    DeliveryStatsResponse,
    OptOutRequest,
)

router = APIRouter()


def _contact_to_response(contact) -> SMSContactResponse:
    tags = contact.tags
    if isinstance(tags, dict):
        tags = list(tags.keys()) if tags else None
    return SMSContactResponse(
        id=contact.id,
        phone_number=contact.phone_number,
        first_name=contact.first_name,
        last_name=contact.last_name,
        tags=tags,
        custom_fields=contact.custom_fields,
        is_opted_in=contact.is_opted_in,
        created_at=contact.created_at,
    )


def _campaign_to_response(campaign) -> SMSCampaignResponse:
    list_ids = campaign.list_ids
    if isinstance(list_ids, dict) and "ids" in list_ids:
        list_ids = list_ids.get("ids", [])
    elif not isinstance(list_ids, list):
        list_ids = list_ids or []
    stats = SMSCampaignStats(
        sent=campaign.sent_count or 0,
        delivered=campaign.delivered_count or 0,
        failed=campaign.failed_count or 0,
        opt_out=campaign.opt_out_count or 0,
    )
    return SMSCampaignResponse(
        id=campaign.id,
        name=campaign.name,
        template_id=campaign.template_id,
        body=campaign.body,
        list_ids=list_ids,
        status=campaign.status.value if hasattr(campaign.status, "value") else str(campaign.status),
        scheduled_at=campaign.scheduled_at,
        sent_at=campaign.sent_at,
        stats=stats,
        created_by=campaign.created_by,
        created_at=campaign.created_at,
    )


# --- Contacts ---
@router.get("/contacts", response_model=dict)
async def list_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    list_id: int | None = None,
    is_opted_in: bool | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> dict:
    """List SMS contacts with pagination/search."""
    svc = SMSContactService(db)
    items, total = await svc.list_contacts(
        skip=skip,
        limit=limit,
        search=search,
        list_id=list_id,
        is_opted_in=is_opted_in,
    )
    return {
        "items": [_contact_to_response(c) for c in items],
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.post("/contacts", response_model=SMSContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    data: SMSContactCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> SMSContactResponse:
    """Create SMS contact."""
    svc = SMSContactService(db)
    try:
        contact = await svc.create_contact(data)
        return _contact_to_response(contact)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/contacts/import")
async def bulk_import_contacts(
    data: ImportContactsRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> dict:
    """Bulk import contacts."""
    svc = SMSContactService(db)
    created, skipped = await svc.import_contacts(data.contacts)
    return {"created": created, "skipped": skipped}


# --- Lists ---
@router.get("/lists", response_model=dict)
async def list_contact_lists(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> dict:
    """List contact lists."""
    svc = SMSListService(db)
    items, total = await svc.list_lists(skip=skip, limit=limit, search=search)
    return {
        "items": [SMSContactListResponse.model_validate(i) for i in items],
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.post("/lists", response_model=SMSContactListResponse, status_code=status.HTTP_201_CREATED)
async def create_contact_list(
    data: SMSContactListCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> SMSContactListResponse:
    """Create contact list."""
    svc = SMSListService(db)
    lst = await svc.create_list(data)
    return SMSContactListResponse.model_validate(lst)


@router.post("/lists/{list_id}/members")
async def add_members_to_list(
    list_id: int,
    contact_ids: list[int],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> dict:
    """Add members to contact list."""
    svc = SMSListService(db)
    try:
        added = await svc.add_members(list_id, contact_ids)
        return {"added": added}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# --- Templates ---
@router.get("/templates", response_model=dict)
async def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> dict:
    """List SMS templates."""
    svc = SMSTemplateService(db)
    items, total = await svc.list_templates(
        skip=skip, limit=limit, category=category, search=search
    )
    return {
        "items": [SMSTemplateResponse.model_validate(i) for i in items],
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.post("/templates", response_model=SMSTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: SMSTemplateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> SMSTemplateResponse:
    """Create SMS template."""
    svc = SMSTemplateService(db)
    template = await svc.create_template(data)
    return SMSTemplateResponse.model_validate(template)


@router.put("/templates/{template_id}", response_model=SMSTemplateResponse)
async def update_template(
    template_id: int,
    data: SMSTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> SMSTemplateResponse:
    """Update SMS template."""
    svc = SMSTemplateService(db)
    template = await svc.update_template(template_id, data)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return SMSTemplateResponse.model_validate(template)


# --- Campaigns ---
@router.get("/campaigns", response_model=SMSCampaignListResponse)
async def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> SMSCampaignListResponse:
    """List SMS campaigns."""
    svc = SMSCampaignService(db)
    items, total = await svc.list_campaigns(
        skip=skip, limit=limit, status=status, search=search
    )
    return SMSCampaignListResponse(
        items=[_campaign_to_response(c) for c in items],
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.post("/campaigns", response_model=SMSCampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: SMSCampaignCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> SMSCampaignResponse:
    """Create SMS campaign."""
    svc = SMSCampaignService(db)
    campaign = await svc.create_campaign(data, created_by=user.id)
    return _campaign_to_response(campaign)


@router.post("/campaigns/{campaign_id}/send")
async def trigger_campaign_send(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> dict:
    """Trigger campaign send (queues messages for async processing)."""
    svc = SMSCampaignService(db)
    campaign = await svc.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    send_svc = SMSSendService(db)
    queued = await send_svc.send_campaign(campaign_id)
    from ...tasks.sms_tasks import send_sms_campaign
    send_sms_campaign.delay(campaign_id)
    return {"message": "Campaign send triggered", "campaign_id": campaign_id, "queued": queued}


@router.get("/campaigns/{campaign_id}/stats", response_model=SMSCampaignStats)
async def get_campaign_stats(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> SMSCampaignStats:
    """Get campaign delivery statistics."""
    svc = SMSCampaignService(db)
    stats = await svc.get_stats(campaign_id)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return stats


# --- Opt-out ---
@router.post("/opt-out")
async def add_opt_out(
    data: OptOutRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> dict:
    """Add phone to opt-out list."""
    svc = OptOutService(db)
    opt_out = await svc.add_opt_out(data.phone, reason=data.reason)
    return {"message": "Phone opted out", "phone_number": opt_out.phone_number}


@router.get("/opt-out/check/{phone}")
async def check_opt_out(
    phone: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> dict:
    """Check if phone is opted out."""
    svc = OptOutService(db)
    is_opted_out = await svc.is_opted_out(phone)
    return {"phone_number": phone, "is_opted_out": is_opted_out}
