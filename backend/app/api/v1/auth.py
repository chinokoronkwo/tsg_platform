from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse, RefreshRequest,
    SocialLoginRequest, OTPVerifyRequest, OTPSendRequest, UserResponse,
)
from ...services.auth_service import AuthService
from ...middleware.auth import get_current_user
from ...models.user import User

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    auth = AuthService(db)
    try:
        user = await auth.register(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return auth.create_tokens(user)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    auth = AuthService(db)
    user = await auth.authenticate(data.email, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return auth.create_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    auth = AuthService(db)
    tokens = await auth.refresh_tokens(data.refresh_token)
    if not tokens:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return tokens


@router.post("/social-login", response_model=TokenResponse)
async def social_login(data: SocialLoginRequest, db: AsyncSession = Depends(get_db)):
    auth = AuthService(db)
    # In production, validate the token with the provider's API
    # For now, extract info from the token payload
    user = await auth.social_login(
        provider=data.provider,
        provider_user_id=data.token[:32],
        email=f"{data.token[:8]}@placeholder.com",
        name="Social User",
    )
    return auth.create_tokens(user)


@router.post("/send-otp")
async def send_otp(data: OTPSendRequest, db: AsyncSession = Depends(get_db)):
    auth = AuthService(db)
    user = await auth.get_user_by_id(data.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    code = await auth.generate_otp(user.id, data.purpose)
    # In production, send via SMS (Twilio) or email
    return {"message": "OTP sent", "user_id": user.id}


@router.post("/verify-otp")
async def verify_otp(data: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    auth = AuthService(db)
    valid = await auth.verify_otp(data.user_id, data.code, data.purpose)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    user = await auth.get_user_by_id(data.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return auth.create_tokens(user)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    from ...services.auth_service import AuthService
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


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)):
    return {"message": "Logged out successfully"}
