"""Celery task stubs for email operations."""

from app.core.celery_app import celery_app


@celery_app.task(name="send_email_campaign")
def send_email_campaign(campaign_id: int) -> dict:
    """Send email campaign to all subscribers in target lists.
    Stub: would use EmailCampaignService + SendGrid/settings.SENDGRID_API_KEY.
    """
    return {"campaign_id": campaign_id, "status": "stub"}


@celery_app.task(name="send_transactional_email")
def send_transactional_email(to: str, subject: str, body: str) -> dict:
    """Send transactional email.
    Stub: would use SendGrid/settings.SENDGRID_API_KEY.
    """
    return {"to": to, "subject": subject, "status": "stub"}
