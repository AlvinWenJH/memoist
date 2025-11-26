from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.settings import get_settings
import hashlib

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt_sha256", "bcrypt"],
    deprecated="auto",
    pbkdf2_sha256__default_rounds=310000,
    bcrypt__truncate_error=False,
    bcrypt_sha256__truncate_error=False,
)
settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    scheme = pwd_context.identify(hashed_password)
    if scheme == "bcrypt" and len(plain_password.encode("utf-8")) > 72:
        pre = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
        return pwd_context.verify(pre, hashed_password)
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except ValueError as e:
        if "72 bytes" in str(e):
            pre = hashlib.sha256(password.encode("utf-8")).hexdigest()
            return pwd_context.hash(pre)
        raise


def create_access_token(
    subject: str, expires_minutes: Optional[int] = None, extra: Optional[dict] = None
) -> str:
    expire_delta = timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {"sub": subject, "exp": datetime.now(timezone.utc) + expire_delta}
    if extra:
        to_encode.update(extra)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

def create_refresh_token(subject: str, expires_days: Optional[int] = None, extra: Optional[dict] = None) -> str:
    expire_delta = timedelta(days=expires_days or settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": subject, "type": "refresh", "exp": datetime.now(timezone.utc) + expire_delta}
    if extra:
        to_encode.update(extra)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
