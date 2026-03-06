"""Admin API endpoints."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from ...core.database import get_db
from ...core.config import get_settings
from ...core.redis import redis_client
from ...middleware.auth import require_admin
from ...middleware.audit import log_action, AUDIT_ACTIONS
from ...models.user import User
from ...models.commerce import Order, Membership
from ...models.commerce import OrderStatus
from ...models.lms import Enrollment, Course
from ...models.lms import CourseStatus
from ...models.audit import AuditLog

router = APIRouter()
settings = get_settings()


@router.get("/dashboard")
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Dashboard stats: total users, active memberships, total orders, revenue, enrollments, active courses."""
    now = datetime.now(timezone.utc)

    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    active_memberships_query = select(func.count(Membership.id)).where(
        Membership.status == "active",
        (Membership.expires_at.is_(None)) | (Membership.expires_at > now),
    )
    active_members_result = await db.execute(active_memberships_query)
    active_memberships = active_members_result.scalar() or 0

    total_orders_result = await db.execute(select(func.count(Order.id)))
    total_orders = total_orders_result.scalar() or 0

    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Order.total), 0)).where(
            Order.status == OrderStatus.COMPLETED
        )
    )
    total_revenue = float(revenue_result.scalar() or 0)

    enrollments_result = await db.execute(select(func.count(Enrollment.id)))
    total_enrollments = enrollments_result.scalar() or 0

    active_courses_result = await db.execute(
        select(func.count(Course.id)).where(Course.status == CourseStatus.PUBLISHED)
    )
    active_courses = active_courses_result.scalar() or 0

    return {
        "total_users": total_users,
        "active_memberships": active_memberships,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_enrollments": total_enrollments,
        "active_courses": active_courses,
    }


@router.get("/audit-log")
async def audit_log(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_id: int | None = Query(None),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
) -> dict:
    """List audit log entries with filters and pagination."""
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    if user_id is not None:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
        count_query = count_query.where(AuditLog.resource_type == resource_type)
    if date_from is not None:
        query = query.where(AuditLog.created_at >= date_from)
        count_query = count_query.where(AuditLog.created_at >= date_from)
    if date_to is not None:
        query = query.where(AuditLog.created_at <= date_to)
        count_query = count_query.where(AuditLog.created_at <= date_to)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    entries = result.scalars().all()

    items = [
        {
            "id": e.id,
            "user_id": e.user_id,
            "action": e.action,
            "resource_type": e.resource_type,
            "resource_id": e.resource_id,
            "details": e.details,
            "ip_address": e.ip_address,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]
    return {"items": items, "total": total}


class SettingsUpdate(BaseModel):
    """Key-value settings update. Extend as needed."""

    key: str
    value: Any


@router.get("/settings")
async def get_settings_route(
    current_user: User = Depends(require_admin),
) -> dict:
    """Return app settings (from config, non-sensitive)."""
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "debug": settings.DEBUG,
    }


@router.put("/settings")
async def update_settings(
    body: SettingsUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Update settings (admin only). Placeholder - extend to persist to Redis/DB."""
    await log_action(
        db,
        user_id=current_user.id,
        action=AUDIT_ACTIONS["settings_change"],
        resource_type="settings",
        resource_id=None,
        details={"key": body.key},
        request=request,
    )
    return {
        "message": "Settings update received",
        "key": body.key,
        "status": "ok",
    }


@router.post("/backup")
async def create_backup(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Trigger database backup. Returns status."""
    try:
        await db.execute(select(1))
        await log_action(
            db,
            user_id=current_user.id,
            action="backup.create",
            resource_type="database",
            resource_id=None,
            details={"trigger": "manual"},
            request=request,
        )
        return {
            "status": "ok",
            "message": "Backup trigger placeholder - integrate with pg_dump or backup service",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database check failed: {str(e)}",
        )


@router.get("/health")
async def system_health(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """System health check (DB, Redis connectivity)."""
    db_ok = False
    redis_ok = False
    db_error = None
    redis_error = None

    try:
        await db.execute(select(1))
        db_ok = True
    except Exception as e:
        db_error = str(e)

    try:
        await redis_client.ping()
        redis_ok = True
    except Exception as e:
        redis_error = str(e)

    healthy = db_ok and redis_ok
    return {
        "status": "healthy" if healthy else "degraded",
        "database": {"ok": db_ok, "error": db_error},
        "redis": {"ok": redis_ok, "error": redis_error},
    }
