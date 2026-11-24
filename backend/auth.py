import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session

from models import AuditLog

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev_fallback_secret_change_in_prod_32chars")
PASSWORD_PEPPER = os.getenv("PASSWORD_PEPPER", "dev_fallback_pepper_change_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    peppered = f"{plain_password}{PASSWORD_PEPPER}"
    return pwd_context.hash(peppered)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    peppered = f"{plain_password}{PASSWORD_PEPPER}"
    return pwd_context.verify(peppered, hashed_password)


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access" or "sub" not in payload:
            return None
        return payload
    except JWTError:
        return None


def generate_refresh_token() -> tuple[str, str]:
    """Returns (raw_token_for_cookie, sha256_hash_for_db)."""
    raw_token = secrets.token_urlsafe(48)
    token_hash = hash_refresh_token(raw_token)
    return raw_token, token_hash


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def get_client_info(request: Request) -> tuple[str, str]:
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    user_agent = request.headers.get("user-agent", "unknown")[:250]
    return ip, user_agent


def record_audit_log(
    db: Session,
    action: str,
    details: str,
    request: Request,
    user_id: Optional[int] = None,
    actor_email: str = "anonymous",
):
    ip, user_agent = get_client_info(request)
    log = AuditLog(
        user_id=user_id,
        actor_email=actor_email,
        action=action,
        details=details,
        ip_address=ip,
        user_agent=user_agent,
    )
    db.add(log)
    db.commit()