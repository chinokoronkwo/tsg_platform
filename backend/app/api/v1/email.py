"""Email API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...middleware.auth import get_current_user, require_admin, require_staff
from ...models.user import User
from ...services.email_service import (
    EmailListService,
    EmailTemplateService,
    EmailCampaignService,
)
from ...schemas.email import (
    EmailListCreate,
    EmailListResponse,
    EmailSubscriberCreate,
    EmailSubscriberResponse,
    EmailTemplateCreate,
    EmailTemplateUpdate,
    EmailTemplateResponse,
    EmailCampaignCreate,
    EmailCampaignResponse,
    EmailCampaignListResponse,
    EmailCampaignStats,
)

router = APIRouter()


def _campaign_to_response(campaign) -> EmailCampaignResponse:
    list_ids = campaign.list_ids
    if isinstance(list_ids, dict) and "ids" in list_ids:
        list_ids = list_ids.get("ids", [])
    elif not isinstance(list_ids, list):
        list_ids = list_ids or []
    stats = EmailCampaignStats(
        sent_count=campaign.sent_count or 0,
        open_count=campaign.open_count or 0,
        click_count=campaign.click_count or 0,
    )
    return EmailCampaignResponse(
        id=campaign.id,
        name=campaign.name,
        subject=campaign.subject,
        template_id=campaign.template_id,
        list_ids=list_ids,
        status=campaign.status.value if hasattr(campaign.status, "value") else str(campaign.status),
        scheduled_at=campaign.scheduled_at,
        sent_at=campaign.sent_at,
        stats=stats,
        created_by=campaign.created_by,
        created_at=campaign.created_at,
    )


# --- Lists ---
@router.get("/lists", response_model=dict)
async def list_email_lists(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> dict:
    """List email lists."""
    svc = EmailListService(db)
    items, total = await svc.list_lists(skip=skip, limit=limit, search=search)
    return {
        "items": [EmailListResponse.model_validate(i) for i in items],
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.post("/lists", response_model=EmailListResponse, status_code=status.HTTP_201_CREATED)
async def create_email_list(
    data: EmailListCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> EmailListResponse:
    """Create email list."""
    svc = EmailListService(db)
    lst = await svc.create_list(data)
    return EmailListResponse.model_validate(lst)


@router.post("/lists/{list_id}/subscribers", response_model=EmailSubscriberResponse, status_code=status.HTTP_201_CREATED)
async def add_subscriber_to_list(
    list_id: int,
    data: EmailSubscriberCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> EmailSubscriberResponse:
    """Add subscriber to email list."""
    svc = EmailListService(db)
    try:
        subscriber = await svc.add_subscriber(list_id, data, user_id=user.id)
        return EmailSubscriberResponse.model_validate(subscriber)
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
    """List email templates."""
    svc = EmailTemplateService(db)
    items, total = await svc.list_templates(
        skip=skip, limit=limit, category=category, search=search
    )
    return {
        "items": [EmailTemplateResponse.model_validate(i) for i in items],
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.post("/templates", response_model=EmailTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: EmailTemplateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> EmailTemplateResponse:
    """Create email template."""
    svc = EmailTemplateService(db)
    template = await svc.create_template(data)
    return EmailTemplateResponse.model_validate(template)


@router.put("/templates/{template_id}", response_model=EmailTemplateResponse)
async def update_template(
    template_id: int,
    data: EmailTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> EmailTemplateResponse:
    """Update email template."""
    svc = EmailTemplateService(db)
    template = await svc.update_template(template_id, data)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return EmailTemplateResponse.model_validate(template)


# --- Campaigns ---
@router.get("/campaigns", response_model=EmailCampaignListResponse)
async def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> EmailCampaignListResponse:
    """List email campaigns."""
    svc = EmailCampaignService(db)
    items, total = await svc.list_campaigns(
        skip=skip, limit=limit, status=status, search=search
    )
    return EmailCampaignListResponse(
        items=[_campaign_to_response(c) for c in items],
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.post("/campaigns", response_model=EmailCampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: EmailCampaignCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> EmailCampaignResponse:
    """Create email campaign."""
    svc = EmailCampaignService(db)
    campaign = await svc.create_campaign(data, created_by=user.id)
    return _campaign_to_response(campaign)


@router.post("/campaigns/{campaign_id}/send")
async def trigger_send(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> dict:
    """Trigger campaign send (queues for async processing)."""
    svc = EmailCampaignService(db)
    campaign = await svc.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    from ...tasks.email_tasks import send_email_campaign
    send_email_campaign.delay(campaign_id)
    return {"message": "Campaign send triggered", "campaign_id": campaign_id}


@router.get("/campaigns/{campaign_id}/stats", response_model=EmailCampaignStats)
async def get_campaign_stats(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    _: User = Depends(require_staff),
) -> EmailCampaignStats:
    """Get campaign statistics."""
    svc = EmailCampaignService(db)
    stats = await svc.get_stats(campaign_id)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return stats
