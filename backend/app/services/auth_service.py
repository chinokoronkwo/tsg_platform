import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from ..core.config import get_settings
from ..models.user import User, Role, SocialAccount, OTPCode, RoleType
from ..schemas.auth import RegisterRequest, TokenResponse, UserResponse

settings = get_settings()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: RegisterRequest) -> User:
        existing = await self.db.execute(select(User).where(User.email == data.email))
        if existing.scalar_one_or_none():
            raise ValueError("Email already registered")

        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            display_name=f"{data.first_name} {data.last_name}",
            phone=data.phone,
        )

        default_role = await self.db.execute(
            select(Role).where(Role.slug == RoleType.CUSTOMER.value)
        )
        role = default_role.scalar_one_or_none()
        if role:
            user.roles.append(role)

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        result = await self.db.execute(
            select(User).options(selectinload(User.roles)).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if not user or not user.hashed_password:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None

        user.last_login = datetime.now(timezone.utc)
        await self.db.commit()
        return user

    def create_tokens(self, user: User) -> TokenResponse:
        role_names = [r.slug for r in user.roles]
        access_token = create_access_token(
            user.id, extra={"roles": role_names, "email": user.email}
        )
        refresh_token = create_refresh_token(user.id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse | None:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None

        user_id = int(payload["sub"])
        result = await self.db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            return None

        return self.create_tokens(user)

    async def get_user_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def social_login(self, provider: str, provider_user_id: str, email: str, name: str) -> User:
        result = await self.db.execute(
            select(SocialAccount).where(
                SocialAccount.provider == provider,
                SocialAccount.provider_user_id == provider_user_id,
            )
        )
        social = result.scalar_one_or_none()

        if social:
            user = await self.get_user_by_id(social.user_id)
            if user:
                user.last_login = datetime.now(timezone.utc)
                await self.db.commit()
                return user

        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            first, _, last = name.partition(" ")
            user = User(
                email=email,
                first_name=first,
                last_name=last or "",
                display_name=name,
                is_verified=True,
            )
            default_role = await self.db.execute(
                select(Role).where(Role.slug == RoleType.CUSTOMER.value)
            )
            role = default_role.scalar_one_or_none()
            if role:
                user.roles.append(role)
            self.db.add(user)
            await self.db.flush()

        social_account = SocialAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
        )
        self.db.add(social_account)
        user.last_login = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def generate_otp(self, user_id: int, purpose: str = "login") -> str:
        code = f"{secrets.randbelow(1000000):06d}"
        otp = OTPCode(
            user_id=user_id,
            code=code,
            purpose=purpose,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        self.db.add(otp)
        await self.db.commit()
        return code

    async def verify_otp(self, user_id: int, code: str, purpose: str = "login") -> bool:
        result = await self.db.execute(
            select(OTPCode).where(
                OTPCode.user_id == user_id,
                OTPCode.code == code,
                OTPCode.purpose == purpose,
                OTPCode.is_used == False,
                OTPCode.expires_at > datetime.now(timezone.utc),
            ).order_by(OTPCode.created_at.desc())
        )
        otp = result.scalar_one_or_none()
        if not otp:
            return False

        otp.is_used = True
        await self.db.commit()
        return True

    def user_to_response(self, user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            display_name=user.display_name,
            phone=user.phone,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_verified=user.is_verified,
            roles=[r.slug for r in user.roles],
            created_at=user.created_at,
        )
