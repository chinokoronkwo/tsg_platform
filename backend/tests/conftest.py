"""Pytest configuration and fixtures for Snob Group backend tests."""

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Set test database URL before any app imports
os.environ.setdefault(
    "DATABASE_URL",
    os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test"),
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.main import app
from app.core.database import get_db, Base
from app.models.user import User, Role
from app.models.user import RoleType
from app.core.security import hash_password, create_access_token


# Create test engine - use same URL as app for CI (PostgreSQL)
_test_db_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
_test_engine = create_async_engine(
    _test_db_url,
    echo=False,
    pool_pre_ping=True,
)
TestSessionLocal = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Async session with transaction rollback for test isolation."""
    async with _test_engine.connect() as conn:
        await conn.begin()
        async with AsyncSession(bind=conn, expire_on_commit=False) as session:
            yield session
        await conn.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """HTTP client configured with FastAPI TestClient (httpx AsyncClient)."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


async def _ensure_roles(session: AsyncSession) -> tuple[Role | None, Role | None]:
    """Ensure customer and administrator roles exist. Returns (customer_role, admin_role)."""
    from sqlalchemy import select
    cust = await session.execute(select(Role).where(Role.slug == RoleType.CUSTOMER.value))
    customer_role = cust.scalar_one_or_none()
    admin = await session.execute(select(Role).where(Role.slug == "administrator"))
    admin_role = admin.scalar_one_or_none()

    if not customer_role:
        customer_role = Role(name="Customer", slug=RoleType.CUSTOMER.value, is_default=True)
        session.add(customer_role)
        await session.flush()
    if not admin_role:
        admin_role = Role(name="Administrator", slug="administrator")
        session.add(admin_role)
        await session.flush()
    return customer_role, admin_role


@pytest_asyncio.fixture
async def auth_headers(db_session):
    """Create a test user and return auth headers with JWT."""
    from sqlalchemy import select

    customer_role, _ = await _ensure_roles(db_session)
    user = User(
        email="testuser@example.com",
        hashed_password=hash_password("TestPassword123!"),
        first_name="Test",
        last_name="User",
        display_name="Test User",
        is_active=True,
    )
    if customer_role:
        user.roles.append(customer_role)
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)

    token = create_access_token(user.id, extra={"roles": [r.slug for r in user.roles], "email": user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(db_session):
    """Create an admin user with administrator role and return auth headers."""
    from sqlalchemy import select

    _, admin_role = await _ensure_roles(db_session)
    admin_user = User(
        email="admin@example.com",
        hashed_password=hash_password("AdminPassword123!"),
        first_name="Admin",
        last_name="User",
        display_name="Admin User",
        is_active=True,
        is_superuser=True,
    )
    if admin_role:
        admin_user.roles.append(admin_role)
    db_session.add(admin_user)
    await db_session.flush()
    await db_session.refresh(admin_user)

    token = create_access_token(
        admin_user.id,
        extra={"roles": [r.slug for r in admin_user.roles], "email": admin_user.email},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def staff_headers(db_session):
    """Create a staff user (gfb_staff) for LMS tests."""
    from sqlalchemy import select

    _, admin_role = await _ensure_roles(db_session)
    staff_role = await db_session.execute(select(Role).where(Role.slug == "gfb_staff"))
    staff_role = staff_role.scalar_one_or_none()
    if not staff_role:
        staff_role = Role(name="GFB Staff", slug="gfb_staff")
        db_session.add(staff_role)
        await db_session.flush()

    staff_user = User(
        email="staff@example.com",
        hashed_password=hash_password("StaffPassword123!"),
        first_name="Staff",
        last_name="User",
        display_name="Staff User",
        is_active=True,
    )
    staff_user.roles.append(staff_role)
    db_session.add(staff_user)
    await db_session.flush()
    await db_session.refresh(staff_user)

    token = create_access_token(
        staff_user.id,
        extra={"roles": [r.slug for r in staff_user.roles], "email": staff_user.email},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create all tables before running tests. Run alembic in CI for migrations."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await _test_engine.dispose()
