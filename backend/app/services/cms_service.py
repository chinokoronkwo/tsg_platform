from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from python_slugify import slugify

from ..models.cms import (
    Page,
    PageSection,
    PageRevision,
    PageStatus,
    Menu,
    MenuItem,
    Media,
    Redirect,
    SEOMetadata,
)
from ..schemas.cms import (
    PageCreate,
    PageUpdate,
    PageSectionCreate,
    MenuCreate,
    MenuItemCreate,
    RedirectCreate,
    SEOMetadataCreate,
)


class PageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_pages(
        self,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Page], int]:
        query = select(Page)
        if status:
            try:
                status_enum = PageStatus(status)
                query = query.where(Page.status == status_enum)
            except ValueError:
                pass
        if search:
            query = query.where(Page.title.ilike(f"%{search}%"))
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = (
            query.options(selectinload(Page.sections))
            .offset(skip)
            .limit(limit)
            .order_by(Page.sort_order, Page.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_page(self, page_id: int) -> Page | None:
        result = await self.db.execute(
            select(Page)
            .options(selectinload(Page.sections))
            .where(Page.id == page_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Page | None:
        result = await self.db.execute(
            select(Page)
            .options(selectinload(Page.sections))
            .where(Page.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create_page(self, data: PageCreate, author_id: int) -> Page:
        slug = data.slug or slugify(data.title)
        existing = await self._get_by_slug(slug)
        if existing:
            from datetime import datetime, timezone
            slug = f"{slug}-{int(datetime.now(timezone.utc).timestamp())}"
        status_enum = PageStatus(data.status) if data.status else PageStatus.DRAFT
        page = Page(
            title=data.title,
            slug=slug,
            status=status_enum,
            template=data.template,
            parent_id=data.parent_id,
            author_id=author_id,
        )
        self.db.add(page)
        await self.db.flush()
        for i, sec in enumerate(data.sections or []):
            section = PageSection(
                page_id=page.id,
                block_type=sec.block_type,
                content=sec.content,
                settings=sec.settings,
                sort_order=sec.sort_order if sec.sort_order else i,
            )
            self.db.add(section)
        await self._create_revision(page, author_id, sections_data=[s.model_dump() for s in (data.sections or [])])
        await self.db.commit()
        await self.db.refresh(page)
        await self.db.refresh(page, ["sections"])
        return page

    async def _get_by_slug(self, slug: str) -> Page | None:
        result = await self.db.execute(select(Page).where(Page.slug == slug))
        return result.scalar_one_or_none()

    async def update_page(self, page_id: int, data: PageUpdate, author_id: int) -> Page | None:
        page = await self.get_page(page_id)
        if not page:
            return None
        if data.title is not None:
            page.title = data.title
        if data.slug is not None:
            page.slug = data.slug
        if data.status is not None:
            try:
                page.status = PageStatus(data.status)
            except ValueError:
                pass
        if data.template is not None:
            page.template = data.template
        if data.parent_id is not None:
            page.parent_id = data.parent_id
        if data.sections is not None:
            await self.db.execute(delete(PageSection).where(PageSection.page_id == page_id))
            for i, sec in enumerate(data.sections):
                section = PageSection(
                    page_id=page.id,
                    block_type=sec.block_type,
                    content=sec.content,
                    settings=sec.settings,
                    sort_order=sec.sort_order if sec.sort_order else i,
                )
                self.db.add(section)
        await self._create_revision(page, author_id)
        await self.db.commit()
        await self.db.refresh(page)
        await self.db.refresh(page, ["sections"])
        return page

    async def _create_revision(
        self,
        page: Page,
        author_id: int,
        sections_data: list[dict] | None = None,
    ) -> None:
        if sections_data is None:
            sections_data = [
                {
                    "block_type": s.block_type,
                    "content": s.content,
                    "settings": s.settings,
                    "sort_order": s.sort_order,
                }
                for s in page.sections
            ]
        revision_data = {
            "title": page.title,
            "slug": page.slug,
            "status": page.status.value if hasattr(page.status, "value") else str(page.status),
            "template": page.template,
            "parent_id": page.parent_id,
            "sections": sections_data or [],
        }
        rev = PageRevision(
            page_id=page.id,
            revision_data=revision_data,
            author_id=author_id,
        )
        self.db.add(rev)

    async def list_revisions(self, page_id: int) -> list[PageRevision]:
        result = await self.db.execute(
            select(PageRevision)
            .where(PageRevision.page_id == page_id)
            .order_by(PageRevision.created_at.desc())
        )
        return list(result.scalars().all())

    async def restore_revision(self, page_id: int, rev_id: int, author_id: int) -> Page | None:
        result = await self.db.execute(
            select(PageRevision).where(
                PageRevision.id == rev_id,
                PageRevision.page_id == page_id,
            )
        )
        rev = result.scalar_one_or_none()
        if not rev:
            return None
        data = rev.revision_data
        update = PageUpdate(
            title=data.get("title"),
            slug=data.get("slug"),
            status=data.get("status"),
            template=data.get("template"),
            parent_id=data.get("parent_id"),
            sections=[PageSectionCreate(**s) for s in data.get("sections", [])] if data.get("sections") else None,
        )
        return await self.update_page(page_id, update, author_id)


class MenuService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_menus(self) -> list[Menu]:
        result = await self.db.execute(
            select(Menu)
            .options(
                selectinload(Menu.items)
                .selectinload(MenuItem.children)
                .selectinload(MenuItem.children),
            )
            .order_by(Menu.name)
        )
        return list(result.scalars().unique().all())

    async def get_menu(self, menu_id: int) -> Menu | None:
        result = await self.db.execute(
            select(Menu)
            .options(
                selectinload(Menu.items)
                .selectinload(MenuItem.children)
                .selectinload(MenuItem.children),
            )
            .where(Menu.id == menu_id)
        )
        return result.scalar_one_or_none()

    async def create_menu(self, data: MenuCreate) -> Menu:
        menu = Menu(
            name=data.name,
            slug=data.slug,
            location=data.location,
        )
        self.db.add(menu)
        await self.db.flush()
        await self._sync_items(menu.id, data.items)
        await self.db.commit()
        await self.db.refresh(menu)
        await self.db.refresh(menu, ["items"])
        return menu

    async def update_menu(self, menu_id: int, data: MenuCreate) -> Menu | None:
        menu = await self.get_menu(menu_id)
        if not menu:
            return None
        menu.name = data.name
        menu.slug = data.slug
        menu.location = data.location
        await self.db.execute(delete(MenuItem).where(MenuItem.menu_id == menu_id))
        await self._sync_items(menu.id, data.items)
        await self.db.commit()
        await self.db.refresh(menu)
        await self.db.refresh(menu, ["items"])
        return menu

    async def _sync_items(self, menu_id: int, items: list[MenuItemCreate], parent_id: int | None = None) -> None:
        for i, item_data in enumerate(items):
            item = MenuItem(
                menu_id=menu_id,
                parent_id=parent_id,
                label=item_data.label,
                url=item_data.url,
                page_id=item_data.page_id,
                target=item_data.target,
                css_class=item_data.css_class,
                sort_order=item_data.sort_order if item_data.sort_order else i,
            )
            self.db.add(item)
            await self.db.flush()
            if item_data.children:
                await self._sync_items(menu_id, item_data.children, parent_id=item.id)


class MediaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_media(
        self,
        skip: int = 0,
        limit: int = 20,
        folder: str | None = None,
    ) -> tuple[list[Media], int]:
        query = select(Media)
        if folder:
            query = query.where(Media.folder == folder)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset(skip).limit(limit).order_by(Media.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def create_record(
        self,
        filename: str,
        original_filename: str,
        url: str,
        mime_type: str,
        file_size: int,
        uploaded_by: int,
        width: int | None = None,
        height: int | None = None,
        alt_text: str | None = None,
        caption: str | None = None,
        folder: str | None = None,
    ) -> Media:
        media = Media(
            filename=filename,
            original_filename=original_filename,
            url=url,
            mime_type=mime_type,
            file_size=file_size,
            uploaded_by=uploaded_by,
            width=width,
            height=height,
            alt_text=alt_text,
            caption=caption,
            folder=folder,
        )
        self.db.add(media)
        await self.db.commit()
        await self.db.refresh(media)
        return media

    async def delete_record(self, media_id: int) -> bool:
        result = await self.db.execute(select(Media).where(Media.id == media_id))
        media = result.scalar_one_or_none()
        if not media:
            return False
        await self.db.delete(media)
        await self.db.commit()
        return True


class RedirectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_redirects(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Redirect], int]:
        query = select(Redirect)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset(skip).limit(limit).order_by(Redirect.source_path)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def create_redirect(self, data: RedirectCreate) -> Redirect:
        redirect = Redirect(
            source_path=data.source_path,
            target_path=data.target_path,
            status_code=data.status_code,
            is_active=data.is_active,
        )
        self.db.add(redirect)
        await self.db.commit()
        await self.db.refresh(redirect)
        return redirect

    async def get_redirect(self, redirect_id: int) -> Redirect | None:
        result = await self.db.execute(select(Redirect).where(Redirect.id == redirect_id))
        return result.scalar_one_or_none()

    async def update_redirect(self, redirect_id: int, data: RedirectCreate) -> Redirect | None:
        redirect = await self.get_redirect(redirect_id)
        if not redirect:
            return None
        redirect.source_path = data.source_path
        redirect.target_path = data.target_path
        redirect.status_code = data.status_code
        redirect.is_active = data.is_active
        await self.db.commit()
        await self.db.refresh(redirect)
        return redirect

    async def delete_redirect(self, redirect_id: int) -> bool:
        redirect = await self.get_redirect(redirect_id)
        if not redirect:
            return False
        await self.db.delete(redirect)
        await self.db.commit()
        return True

    async def lookup_by_path(self, source_path: str) -> Redirect | None:
        result = await self.db.execute(
            select(Redirect).where(
                Redirect.source_path == source_path,
                Redirect.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()


class SEOService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_page(self, page_id: int) -> SEOMetadata | None:
        result = await self.db.execute(
            select(SEOMetadata).where(SEOMetadata.page_id == page_id)
        )
        return result.scalar_one_or_none()

    async def get_for_entity(self, entity_type: str, entity_id: int) -> SEOMetadata | None:
        result = await self.db.execute(
            select(SEOMetadata).where(
                SEOMetadata.entity_type == entity_type,
                SEOMetadata.entity_id == entity_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_for_page(self, page_id: int, data: SEOMetadataCreate) -> SEOMetadata:
        existing = await self.get_for_page(page_id)
        if existing:
            existing.title = data.title
            existing.description = data.description
            existing.canonical_url = data.canonical_url
            existing.og_title = data.og_title
            existing.og_description = data.og_description
            existing.og_image = data.og_image
            existing.json_ld = data.json_ld
            existing.no_index = data.no_index
            existing.no_follow = data.no_follow
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        seo = SEOMetadata(
            page_id=page_id,
            title=data.title,
            description=data.description,
            canonical_url=data.canonical_url,
            og_title=data.og_title,
            og_description=data.og_description,
            og_image=data.og_image,
            json_ld=data.json_ld,
            no_index=data.no_index,
            no_follow=data.no_follow,
        )
        self.db.add(seo)
        await self.db.commit()
        await self.db.refresh(seo)
        return seo

    async def update_for_entity(
        self, entity_type: str, entity_id: int, data: SEOMetadataCreate
    ) -> SEOMetadata:
        existing = await self.get_for_entity(entity_type, entity_id)
        if existing:
            existing.title = data.title
            existing.description = data.description
            existing.canonical_url = data.canonical_url
            existing.og_title = data.og_title
            existing.og_description = data.og_description
            existing.og_image = data.og_image
            existing.json_ld = data.json_ld
            existing.no_index = data.no_index
            existing.no_follow = data.no_follow
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        seo = SEOMetadata(
            entity_type=entity_type,
            entity_id=entity_id,
            title=data.title,
            description=data.description,
            canonical_url=data.canonical_url,
            og_title=data.og_title,
            og_description=data.og_description,
            og_image=data.og_image,
            json_ld=data.json_ld,
            no_index=data.no_index,
            no_follow=data.no_follow,
        )
        self.db.add(seo)
        await self.db.commit()
        await self.db.refresh(seo)
        return seo
