import secrets
import hashlib
import hmac as hmac_lib
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    claims = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": settings.APP_NAME,
    }
    if extra_claims:
        claims.update(extra_claims)
    return jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def generate_api_key() -> str:
    return f"aqp_{secrets.token_urlsafe(32)}"


def generate_hmac_signature(payload: str, secret: str) -> str:
    return hmac_lib.new(
        secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
