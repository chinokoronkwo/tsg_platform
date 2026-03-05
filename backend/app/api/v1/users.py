"""Users API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from ...core.database import get_db
from ...middleware.auth import get_current_user, require_admin
from ...models.user import User, Role
from ...models.audit import AdminUserNote
from ...services.auth_service import AuthService
from ...schemas.auth import UserResponse, UserUpdate, TokenResponse

router = APIRouter()


class AdminNoteCreate(BaseModel):
    note: str


@router.get("/")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    role: str | None = Query(None, description="Filter by role slug"),
) -> dict:
    """List all users with pagination, search, and role filter (admin only)."""
    query = select(User).options(selectinload(User.roles))
    search_filter = None
    if search:
        search_term = f"%{search}%"
        search_filter = or_(
            User.email.ilike(search_term),
            User.first_name.ilike(search_term),
            User.last_name.ilike(search_term),
            User.display_name.ilike(search_term),
            User.username.ilike(search_term),
        )
        query = query.where(search_filter)

    if role:
        query = query.join(User.roles).where(Role.slug == role).distinct()
        count_subq = select(User.id).join(User.roles).where(Role.slug == role)
        if search_filter:
            count_subq = count_subq.where(search_filter)
        count_query = select(func.count()).select_from(count_subq.distinct().subquery())
    else:
        count_query = select(func.count(User.id))
        if search_filter:
            count_query = count_query.where(search_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().unique().all()

    auth_service = AuthService(db)
    items = [auth_service.user_to_response(u) for u in users]

    return {"items": items, "total": total}


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Get user by ID with roles and memberships (admin only)."""
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.roles),
            selectinload(User.memberships),
        )
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    auth_service = AuthService(db)
    user_data = auth_service.user_to_response(user)
    memberships = [
        {
            "id": m.id,
            "plan_id": m.plan_id,
            "status": m.status,
            "starts_at": m.starts_at.isoformat() if m.starts_at else None,
            "expires_at": m.expires_at.isoformat() if m.expires_at else None,
        }
        for m in user.memberships
    ]
    return {
        **user_data.model_dump(),
        "roles": [{"id": r.id, "name": r.name, "slug": r.slug} for r in user.roles],
        "memberships": memberships,
    }


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Update user profile (admin or self)."""
    if current_user.id != user_id and not current_user.is_superuser:
        admin_roles = {r.slug for r in current_user.roles}
        if "administrator" not in admin_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update another user's profile",
            )

    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)

    auth_service = AuthService(db)
    return auth_service.user_to_response(user)


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Deactivate user (admin only, sets is_active=False)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = False
    await db.commit()
    return {"message": "User deactivated", "user_id": user_id}


@router.post("/{user_id}/impersonate")
async def impersonate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> TokenResponse:
    """Generate tokens for another user (admin only)."""
    result = await db.execute(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not target_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot impersonate inactive user",
        )

    auth_service = AuthService(db)
    return auth_service.create_tokens(target_user)


@router.post("/{user_id}/notes")
async def add_admin_note(
    user_id: int,
    body: AdminNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Add admin note to user (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    note = AdminUserNote(
        user_id=user_id,
        author_id=current_user.id,
        note=body.note,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)

    return {
        "id": note.id,
        "user_id": note.user_id,
        "author_id": note.author_id,
        "note": note.note,
        "created_at": note.created_at.isoformat() if note.created_at else None,
    }


@router.get("/{user_id}/notes")
async def list_admin_notes(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    """List admin notes for user (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    count_result = await db.execute(
        select(func.count(AdminUserNote.id)).where(AdminUserNote.user_id == user_id)
    )
    total = count_result.scalar() or 0

    notes_result = await db.execute(
        select(AdminUserNote)
        .where(AdminUserNote.user_id == user_id)
        .order_by(AdminUserNote.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    notes = notes_result.scalars().all()

    items = [
        {
            "id": n.id,
            "user_id": n.user_id,
            "author_id": n.author_id,
            "note": n.note,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notes
    ]
    return {"items": items, "total": total}
