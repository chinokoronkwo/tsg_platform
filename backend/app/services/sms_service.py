"""SMS services for Snob Group platform."""

import re
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.sms import (
    SMSContact,
    SMSContactList,
    SMSContactListMember,
    SMSTemplate,
    SMSCampaign,
    SMSCampaignMessage,
    SMSOptOut,
    SMSCampaignStatus,
    DeliveryStatus,
)
from ..models.user import User
from ..schemas.sms import (
    SMSContactCreate,
    SMSContactListCreate,
    SMSTemplateCreate,
    SMSTemplateUpdate,
    SMSCampaignCreate,
    SMSCampaignStats,
    ImportContactItem,
    DeliveryStatsResponse,
)

# GSM-7: 160 chars per segment; Unicode: 70 chars per segment
GSM_SEGMENT_LENGTH = 160
UNICODE_SEGMENT_LENGTH = 70


def _normalize_phone(phone: str) -> str:
    """Normalize phone number for storage."""
    return re.sub(r"\D", "", phone)


def _is_gsm_only(text: str) -> bool:
    """Check if text uses only GSM-7 characters."""
    gsm_chars = set(
        "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
        "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
    )
    return all(c in gsm_chars for c in text)


def _calculate_sms_segments(body: str) -> tuple[int, int]:
    """Return (character_count, segment_count)."""
    char_count = len(body)
    if _is_gsm_only(body):
        segment_count = (char_count + GSM_SEGMENT_LENGTH - 1) // GSM_SEGMENT_LENGTH or 1
    else:
        segment_count = (char_count + UNICODE_SEGMENT_LENGTH - 1) // UNICODE_SEGMENT_LENGTH or 1
    return char_count, segment_count


class SMSContactService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_contacts(
        self,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        list_id: int | None = None,
        is_opted_in: bool | None = None,
    ) -> tuple[list[SMSContact], int]:
        query = select(SMSContact)
        if search:
            q = f"%{search}%"
            query = query.where(
                (SMSContact.phone_number.ilike(q))
                | (SMSContact.first_name.ilike(q))
                | (SMSContact.last_name.ilike(q))
            )
        if is_opted_in is not None:
            query = query.where(SMSContact.is_opted_in == is_opted_in)
        if list_id:
            query = query.join(SMSContactListMember).where(
                SMSContactListMember.list_id == list_id
            ).distinct()
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset(skip).limit(limit).order_by(SMSContact.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_contact(self, contact_id: int) -> SMSContact | None:
        result = await self.db.execute(
            select(SMSContact).where(SMSContact.id == contact_id)
        )
        return result.scalar_one_or_none()

    async def get_contact_by_phone(self, phone: str) -> SMSContact | None:
        normalized = _normalize_phone(phone)
        result = await self.db.execute(
            select(SMSContact).where(SMSContact.phone_number == normalized)
        )
        return result.scalar_one_or_none()

    async def create_contact(self, data: SMSContactCreate) -> SMSContact:
        phone = _normalize_phone(data.phone_number)
        if not phone:
            raise ValueError("Invalid phone number")
        existing = await self.get_contact_by_phone(phone)
        if existing:
            raise ValueError("Contact with this phone number already exists")
        contact = SMSContact(
            phone_number=phone,
            first_name=data.first_name,
            last_name=data.last_name,
            tags=data.tags,
            custom_fields=data.custom_fields,
            is_opted_in=data.is_opted_in,
            opted_in_at=datetime.now(timezone.utc) if data.is_opted_in else None,
        )
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def import_contacts(
        self,
        contacts: list[ImportContactItem],
    ) -> tuple[int, int]:
        """Bulk create contacts. Returns (created_count, skipped_count)."""
        created = 0
        skipped = 0
        for item in contacts:
            phone = _normalize_phone(item.phone_number)
            if not phone:
                skipped += 1
                continue
            existing = await self.get_contact_by_phone(phone)
            if existing:
                skipped += 1
                continue
            contact = SMSContact(
                phone_number=phone,
                first_name=item.first_name,
                last_name=item.last_name,
                is_opted_in=True,
                opted_in_at=datetime.now(timezone.utc),
            )
            self.db.add(contact)
            created += 1
        await self.db.commit()
        return created, skipped

    async def sync_from_users(self) -> int:
        """Create SMS contacts from users with phone numbers. Returns count synced."""
        result = await self.db.execute(
            select(User).where(User.phone.isnot(None), User.phone != "")
        )
        users = result.scalars().all()
        synced = 0
        for user in users:
            if not user.phone:
                continue
            phone = _normalize_phone(user.phone)
            if not phone:
                continue
            existing = await self.get_contact_by_phone(phone)
            if existing:
                if not existing.user_id:
                    existing.user_id = user.id
                    synced += 1
                continue
            contact = SMSContact(
                phone_number=phone,
                first_name=user.first_name,
                last_name=user.last_name,
                user_id=user.id,
                is_opted_in=True,
                opted_in_at=datetime.now(timezone.utc),
            )
            self.db.add(contact)
            synced += 1
        await self.db.commit()
        return synced


class SMSListService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_lists(
        self,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
    ) -> tuple[list[SMSContactList], int]:
        query = select(SMSContactList)
        if search:
            query = query.where(SMSContactList.name.ilike(f"%{search}%"))
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset(skip).limit(limit).order_by(SMSContactList.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_list(self, list_id: int) -> SMSContactList | None:
        result = await self.db.execute(
            select(SMSContactList).where(SMSContactList.id == list_id)
        )
        return result.scalar_one_or_none()

    async def create_list(self, data: SMSContactListCreate) -> SMSContactList:
        lst = SMSContactList(
            name=data.name,
            description=data.description,
            is_dynamic=data.is_dynamic,
            filter_criteria=data.filter_criteria,
        )
        self.db.add(lst)
        await self.db.commit()
        await self.db.refresh(lst)
        return lst

    async def add_members(
        self,
        list_id: int,
        contact_ids: list[int],
    ) -> int:
        """Add contacts to list. Returns count added."""
        lst = await self.get_list(list_id)
        if not lst:
            raise ValueError("Contact list not found")
        added = 0
        for cid in contact_ids:
            result = await self.db.execute(
                select(SMSContactListMember).where(
                    SMSContactListMember.list_id == list_id,
                    SMSContactListMember.contact_id == cid,
                )
            )
            if result.scalar_one_or_none():
                continue
            member = SMSContactListMember(list_id=list_id, contact_id=cid)
            self.db.add(member)
            added += 1
        lst.member_count = (lst.member_count or 0) + added
        await self.db.commit()
        return added

    async def remove_member(self, list_id: int, contact_id: int) -> bool:
        result = await self.db.execute(
            select(SMSContactListMember).where(
                SMSContactListMember.list_id == list_id,
                SMSContactListMember.contact_id == contact_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return False
        lst = await self.get_list(list_id)
        if lst and lst.member_count:
            lst.member_count -= 1
        await self.db.delete(member)
        await self.db.commit()
        return True


class SMSTemplateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_templates(
        self,
        skip: int = 0,
        limit: int = 20,
        category: str | None = None,
        search: str | None = None,
    ) -> tuple[list[SMSTemplate], int]:
        query = select(SMSTemplate)
        if category:
            query = query.where(SMSTemplate.category == category)
        if search:
            query = query.where(SMSTemplate.name.ilike(f"%{search}%"))
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset(skip).limit(limit).order_by(SMSTemplate.updated_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_template(self, template_id: int) -> SMSTemplate | None:
        result = await self.db.execute(
            select(SMSTemplate).where(SMSTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    def _compute_counts(self, body: str) -> tuple[int, int]:
        char_count, segment_count = _calculate_sms_segments(body)
        return char_count, segment_count

    async def create_template(self, data: SMSTemplateCreate) -> SMSTemplate:
        char_count, segment_count = self._compute_counts(data.body)
        merge = data.merge_fields
        if isinstance(merge, list):
            merge = {m: "" for m in merge} if merge else None
        template = SMSTemplate(
            name=data.name,
            body=data.body,
            category=data.category,
            merge_fields=merge,
            character_count=char_count,
            segment_count=segment_count,
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update_template(
        self,
        template_id: int,
        data: SMSTemplateUpdate,
    ) -> SMSTemplate | None:
        template = await self.get_template(template_id)
        if not template:
            return None
        update_data = data.model_dump(exclude_unset=True)
        if "body" in update_data:
            char_count, segment_count = self._compute_counts(update_data["body"])
            template.character_count = char_count
            template.segment_count = segment_count
        if "merge_fields" in update_data:
            mf = update_data["merge_fields"]
            if isinstance(mf, list):
                update_data["merge_fields"] = {m: "" for m in mf} if mf else None
        for key, value in update_data.items():
            if key != "body" or value is not None:
                setattr(template, key, value)
        await self.db.commit()
        await self.db.refresh(template)
        return template


class SMSCampaignService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_campaigns(
        self,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[SMSCampaign], int]:
        query = select(SMSCampaign)
        if status:
            query = query.where(SMSCampaign.status == status)
        if search:
            query = query.where(SMSCampaign.name.ilike(f"%{search}%"))
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset(skip).limit(limit).order_by(SMSCampaign.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_campaign(self, campaign_id: int) -> SMSCampaign | None:
        result = await self.db.execute(
            select(SMSCampaign)
            .options(selectinload(SMSCampaign.template))
            .where(SMSCampaign.id == campaign_id)
        )
        return result.scalar_one_or_none()

    async def create_campaign(
        self,
        data: SMSCampaignCreate,
        created_by: int,
    ) -> SMSCampaign:
        status_enum = SMSCampaignStatus(data.status) if data.status else SMSCampaignStatus.DRAFT
        campaign = SMSCampaign(
            name=data.name,
            template_id=data.template_id,
            body=data.body,
            list_ids=data.list_ids if data.list_ids else None,
            status=status_enum,
            scheduled_at=data.scheduled_at,
            created_by=created_by,
        )
        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def schedule_campaign(
        self,
        campaign_id: int,
        scheduled_at: datetime,
    ) -> SMSCampaign | None:
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return None
        campaign.status = SMSCampaignStatus.SCHEDULED
        campaign.scheduled_at = scheduled_at
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def get_stats(self, campaign_id: int) -> SMSCampaignStats | None:
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return None
        return SMSCampaignStats(
            sent=campaign.sent_count or 0,
            delivered=campaign.delivered_count or 0,
            failed=campaign.failed_count or 0,
            opt_out=campaign.opt_out_count or 0,
        )


class SMSSendService:
    """SMS sending (placeholder using Twilio)."""

    def __init__(self, db: AsyncSession | None = None):
        self.db = db

    async def send_single(self, phone: str, body: str) -> bool:
        """Send single SMS. Placeholder for Twilio integration."""
        # from ..core.config import get_settings
        # settings = get_settings()
        # if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN: ...
        return True

    async def send_campaign(self, campaign_id: int) -> int:
        """Queue campaign messages for sending. Returns count queued."""
        if not self.db:
            return 0
        campaign = await SMSCampaignService(self.db).get_campaign(campaign_id)
        if not campaign or not campaign.list_ids:
            return 0
        list_ids = campaign.list_ids if isinstance(campaign.list_ids, list) else []
        body = campaign.body or (campaign.template.body if campaign.template else "")
        if not body:
            return 0
        opt_out_svc = OptOutService(self.db)
        contact_svc = SMSContactService(self.db)
        list_svc = SMSListService(self.db)
        queued = 0
        for list_id in list_ids:
            lst = await list_svc.get_list(list_id)
            if not lst:
                continue
            result = await self.db.execute(
                select(SMSContact)
                .join(SMSContactListMember, SMSContact.id == SMSContactListMember.contact_id)
                .where(
                    SMSContactListMember.list_id == list_id,
                    SMSContact.is_opted_in == True,
                )
            )
            for contact in result.scalars().unique().all():
                if await opt_out_svc.is_opted_out(contact.phone_number):
                    continue
                msg = SMSCampaignMessage(
                    campaign_id=campaign_id,
                    contact_id=contact.id,
                    body=body,
                    status=DeliveryStatus.QUEUED,
                )
                self.db.add(msg)
                queued += 1
        campaign.status = SMSCampaignStatus.SENDING
        await self.db.commit()
        return queued


class OptOutService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_opt_out(self, phone: str, reason: str | None = None) -> SMSOptOut:
        normalized = _normalize_phone(phone)
        result = await self.db.execute(
            select(SMSOptOut).where(SMSOptOut.phone_number == normalized)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        opt_out = SMSOptOut(phone_number=normalized, reason=reason)
        self.db.add(opt_out)
        contact_svc = SMSContactService(self.db)
        contact = await contact_svc.get_contact_by_phone(normalized)
        if contact:
            contact.is_opted_in = False
            contact.opted_out_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(opt_out)
        return opt_out

    async def is_opted_out(self, phone: str) -> bool:
        normalized = _normalize_phone(phone)
        result = await self.db.execute(
            select(SMSOptOut).where(SMSOptOut.phone_number == normalized)
        )
        return result.scalar_one_or_none() is not None

    async def handle_stop_keyword(self, phone: str) -> None:
        """Handle STOP keyword from inbound SMS."""
        await self.add_opt_out(phone, reason="STOP keyword")
