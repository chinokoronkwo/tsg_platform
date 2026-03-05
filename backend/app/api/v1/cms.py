"""CMS API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ...core.database import get_db
from ...middleware.auth import get_current_user, require_admin, require_editor
from ...models.user import User
from ...services.cms_service import PageService, MenuService
from ...schemas.cms import (
    PageCreate,
    PageUpdate,
    PageResponse,
    PageListResponse,
    PageRevisionResponse,
    PageSectionResponse,
    MenuCreate,
    MenuResponse,
    MenuItemResponse,
)

router = APIRouter()


def _page_to_response(page) -> PageResponse:
    return PageResponse(
        id=page.id,
        title=page.title,
        slug=page.slug,
        status=page.status.value if hasattr(page.status, "value") else str(page.status),
        template=page.template,
        parent_id=page.parent_id,
        author_id=page.author_id,
        sort_order=page.sort_order,
        published_at=page.published_at,
        scheduled_at=page.scheduled_at,
        created_at=page.created_at,
        updated_at=page.updated_at,
        sections=[
            PageSectionResponse.model_validate(s) for s in page.sections
        ] if page.sections else [],
    )


# --- Pages ---
@router.get("/pages", response_model=PageListResponse)
async def list_pages(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> PageListResponse:
    """List CMS pages with pagination."""
    svc = PageService(db)
    items, total = await svc.list_pages(skip=skip, limit=limit, status=status, search=search)
    return PageListResponse(
        items=[_page_to_response(p) for p in items],
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.post("/pages", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
async def create_page(
    data: PageCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor),
) -> PageResponse:
    """Create a new page (admin/editor)."""
    svc = PageService(db)
    page = await svc.create_page(data, author_id=user.id)
    return _page_to_response(page)


@router.get("/pages/{page_id}/revisions", response_model=list[PageRevisionResponse])
async def list_page_revisions(
    page_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor),
) -> list[PageRevisionResponse]:
    """List revisions for a page."""
    svc = PageService(db)
    page = await svc.get_page(page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
    revisions = await svc.list_revisions(page_id)
    return [PageRevisionResponse.model_validate(r) for r in revisions]


@router.post("/pages/{page_id}/revisions/{rev_id}/restore", response_model=PageResponse)
async def restore_revision(
    page_id: int,
    rev_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor),
) -> PageResponse:
    """Restore a page to a previous revision."""
    svc = PageService(db)
    page = await svc.restore_revision(page_id, rev_id, author_id=user.id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page or revision not found")
    return _page_to_response(page)


@router.put("/pages/{page_id}", response_model=PageResponse)
async def update_page(
    page_id: int,
    data: PageUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor),
) -> PageResponse:
    """Update page (creates revision)."""
    svc = PageService(db)
    page = await svc.update_page(page_id, data, author_id=user.id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
    return _page_to_response(page)


@router.get("/pages/{slug}", response_model=PageResponse)
async def get_page_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> PageResponse:
    """Get page by slug."""
    svc = PageService(db)
    page = await svc.get_by_slug(slug)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
    return _page_to_response(page)


# --- Menus ---
@router.get("/menus", response_model=list[MenuResponse])
async def list_menus(
    db: AsyncSession = Depends(get_db),
) -> list[MenuResponse]:
    """List all menus."""
    svc = MenuService(db)
    menus = await svc.list_menus()
    return [_menu_to_response(m) for m in menus]


@router.post("/menus", response_model=MenuResponse, status_code=status.HTTP_201_CREATED)
async def create_menu(
    data: MenuCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor),
) -> MenuResponse:
    """Create a new menu."""
    svc = MenuService(db)
    menu = await svc.create_menu(data)
    return _menu_to_response(menu)


@router.put("/menus/{menu_id}", response_model=MenuResponse)
async def update_menu(
    menu_id: int,
    data: MenuCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_editor),
) -> MenuResponse:
    """Update a menu."""
    svc = MenuService(db)
    menu = await svc.update_menu(menu_id, data)
    if not menu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu not found")
    return _menu_to_response(menu)


def _menu_to_response(menu) -> MenuResponse:
    root_items = [i for i in (menu.items or []) if i.parent_id is None]
    return MenuResponse(
        id=menu.id,
        name=menu.name,
        slug=menu.slug,
        location=menu.location,
        items=[_menu_item_to_response(i) for i in root_items],
    )


def _menu_item_to_response(item) -> MenuItemResponse:
    children = getattr(item, "children", None) or []
    return MenuItemResponse(
        id=item.id,
        menu_id=item.menu_id,
        parent_id=item.parent_id,
        label=item.label,
        url=item.url,
        page_id=item.page_id,
        target=item.target,
        css_class=item.css_class,
        sort_order=item.sort_order,
        children=[_menu_item_to_response(c) for c in children],
    )
