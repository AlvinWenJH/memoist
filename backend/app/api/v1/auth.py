from typing import List, Optional
from uuid import UUID
from datetime import datetime
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.models.auth import User
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
    create_refresh_token,
)

logger = structlog.get_logger()
router = APIRouter()


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    skip: int
    limit: int


class UserStats(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        uid = UUID(sub)
        res = await db.execute(select(User).where(User.id == uid))
        u = res.scalar_one_or_none()
        if not u:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        return u
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )


def to_user_response(u: User) -> UserResponse:
    return UserResponse(
        id=str(u.id),
        email=u.email,
        username=u.username,
        full_name=u.full_name,
        is_active=u.is_active,
        created_at=u.created_at,
        updated_at=u.updated_at,
        last_login=u.last_login,
    )


@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(User).where(
            (User.email == user_data.email) | (User.username == user_data.username)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User already exists")
    now = datetime.utcnow()
    u = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        is_active=True,
        password_hash=get_password_hash(user_data.password),
        created_at=now,
        updated_at=now,
        last_login=None,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return to_user_response(u)


@router.post("/login", response_model=Token)
async def login_user(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.username == user_data.username))
    u = res.scalar_one_or_none()
    if not u or not verify_password(user_data.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    u.last_login = datetime.utcnow()
    await db.commit()
    access = create_access_token(subject=str(u.id), extra={"username": u.username})
    refresh = create_refresh_token(subject=str(u.id), extra={"username": u.username})
    logger.info("User logged in", username=u.username, email=u.email)
    return Token(access_token=access, refresh_token=refresh, token_type="bearer")


class TokenRefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=Token)
async def refresh_token(data: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid refresh token")
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token")
    uid = UUID(sub)
    res = await db.execute(select(User).where(User.id == uid))
    u = res.scalar_one_or_none()
    if not u or not u.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    access = create_access_token(subject=str(u.id), extra={"username": u.username})
    new_refresh = create_refresh_token(
        subject=str(u.id), extra={"username": u.username}
    )
    return Token(access_token=access, refresh_token=new_refresh, token_type="bearer")


@router.get("/stats", response_model=UserStats)
async def get_user_stats(db: AsyncSession = Depends(get_db)):
    total = await db.execute(select(func.count()).select_from(User))
    total_users = total.scalar() or 0
    active = await db.execute(
        select(func.count()).select_from(User).where(User.is_active == True)
    )
    active_users = active.scalar() or 0
    inactive_users = total_users - active_users
    return UserStats(
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = UUID(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    res = await db.execute(select(User).where(User.id == uid))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return to_user_response(u)


@router.get("/", response_model=UserListResponse)
async def list_users(
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    q = select(User)
    if is_active is not None:
        q = q.where(User.is_active == is_active)
    total_res = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_res.scalar() or 0
    res = await db.execute(q.order_by(User.created_at.desc()).offset(skip).limit(limit))
    users = [to_user_response(u) for u in res.scalars().all()]
    return UserListResponse(users=users, total=total, skip=skip, limit=limit)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str, update_data: UserUpdate, db: AsyncSession = Depends(get_db)
):
    try:
        uid = UUID(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    res = await db.execute(select(User).where(User.id == uid))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    update_dict = update_data.dict(exclude_unset=True)
    if "email" in update_dict or "username" in update_dict:
        conflict_q = select(User).where(User.id != uid)
        if "email" in update_dict:
            conflict_q = conflict_q.where(User.email == update_dict["email"])
        if "username" in update_dict:
            conflict_q = conflict_q.where(User.username == update_dict["username"])
        conflict = await db.execute(conflict_q)
        if conflict.scalar_one_or_none():
            raise HTTPException(
                status_code=409, detail="Email or username already exists"
            )
    if "email" in update_dict:
        u.email = update_dict["email"]
    if "username" in update_dict:
        u.username = update_dict["username"]
    if "full_name" in update_dict:
        u.full_name = update_dict["full_name"]
    if "is_active" in update_dict:
        u.is_active = update_dict["is_active"]
    u.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(u)
    return to_user_response(u)


@router.delete("/{user_id}")
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = UUID(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    res = await db.execute(select(User).where(User.id == uid))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(u)
    await db.commit()
    return {"message": "User deleted successfully"}
