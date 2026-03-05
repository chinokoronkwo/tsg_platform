"""Celery task stubs for SMS operations."""

from app.core.celery_app import celery_app


@celery_app.task(name="send_sms_campaign")
def send_sms_campaign(campaign_id: int) -> dict:
    """Send SMS campaign to all opted-in contacts in target lists.
    Stub: would use SMSCampaignService + Twilio.
    """
    return {"campaign_id": campaign_id, "status": "stub"}


@celery_app.task(name="send_single_sms")
def send_single_sms(phone: str, body: str) -> dict:
    """Send single SMS.
    Stub: would use Twilio.
    """
    return {"phone": phone, "status": "stub"}


@celery_app.task(name="process_sms_webhook")
def process_sms_webhook(data: dict) -> dict:
    """Process inbound SMS webhook (e.g. Twilio status callbacks, STOP handling).
    Stub: would parse webhook payload and update delivery status / opt-out.
    """
    return {"processed": True, "status": "stub"}
