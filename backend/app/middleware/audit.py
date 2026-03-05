"""Audit logging middleware and utilities for admin actions."""

from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.audit import AuditLog


async def log_action(
    db: AsyncSession,
    user_id: int | None,
    action: str,
    resource_type: str,
    resource_id: int | None,
    details: dict[str, Any] | None = None,
    request: Request | None = None,
) -> AuditLog:
    """
    Log an admin action to the audit log.
    Captures: user_id, action, resource_type, resource_id, IP, user_agent, timestamp.
    """
    ip_address = None
    user_agent = None
    if request:
        client_host = request.client.host if request.client else None
        forwarded = request.headers.get("x-forwarded-for")
        ip_address = forwarded.split(",")[0].strip() if forwarded else client_host
        user_agent = request.headers.get("user-agent")

    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)
    return log_entry


# Action constants for consistency
AUDIT_ACTIONS = {
    "user_create": "user.create",
    "user_update": "user.update",
    "user_delete": "user.delete",
    "order_status_change": "order.status_change",
    "payment": "payment",
    "settings_change": "settings.change",
    "impersonation": "impersonation",
    "role_change": "role.change",
}
