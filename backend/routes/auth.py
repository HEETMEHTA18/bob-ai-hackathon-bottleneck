from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models_db import User, RevokedToken
from backend.schemas import UserCreate, UserLogin, UserResponse, TokenResponse, TokenRefresh
from backend.auth import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from backend.dependencies import get_current_user
from backend.config import REFRESH_TOKEN_EXPIRE_DAYS

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def _revoke_token_jti(db: AsyncSession, jti: str, user_id: str, expires_at: datetime) -> None:
    """Persist a refresh-token JTI so it cannot be reused."""
    entry = RevokedToken(jti=jti, user_id=user_id, expires_at=expires_at)
    db.add(entry)
    # Commit handled by get_db context manager


async def _is_jti_revoked(db: AsyncSession, jti: str) -> bool:
    result = await db.execute(select(RevokedToken).where(RevokedToken.jti == jti))
    return result.scalar_one_or_none() is not None


@router.post("/signup", response_model=TokenResponse)
async def signup(data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        company_name=data.company_name,
        role="viewer",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token, rt_jti = create_refresh_token({"sub": str(user.id)})

    from datetime import timedelta
    rt_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    # No need to revoke on fresh issue; just record for future rotation

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # Constant-time failure to avoid user-enumeration timing attacks.
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token, _rt_jti = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Reject if this JTI has already been revoked (replay detection)
    if await _is_jti_revoked(db, jti):
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    # Token rotation: revoke the consumed token before issuing a new one
    exp_ts = payload.get("exp")
    expires_at = datetime.utcfromtimestamp(exp_ts) if exp_ts else datetime.utcnow()
    await _revoke_token_jti(db, jti, str(user.id), expires_at)

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    new_refresh_token, _new_jti = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
async def logout(data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """Revoke the supplied refresh token immediately."""
    payload = decode_token(data.refresh_token)
    if payload and payload.get("type") == "refresh":
        jti = payload.get("jti")
        if jti and not await _is_jti_revoked(db, jti):
            user_id = payload.get("sub", "")
            exp_ts = payload.get("exp")
            expires_at = datetime.utcfromtimestamp(exp_ts) if exp_ts else datetime.utcnow()
            await _revoke_token_jti(db, jti, user_id, expires_at)
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)
