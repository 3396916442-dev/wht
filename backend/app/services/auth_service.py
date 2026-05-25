"""认证业务：验证码、注册、登录。"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timezone
from typing import Sequence

from redis import Redis
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, UserPublic
from app.services.email_service import EmailServiceError, send_verification_email

logger = logging.getLogger("quant.auth")


class AuthError(ValueError):
    """可预期的认证业务错误。"""


def _email_code_key(email: str) -> str:
    return f"email_code:{email.lower()}"


def _email_rate_key(email: str) -> str:
    return f"email_code_rate:{email.lower()}"


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


async def send_email_code(redis: Redis, email: str) -> None:
    """生成验证码写入 Redis 并发送邮件。"""
    email = email.strip().lower()
    rate_key = _email_rate_key(email)
    if redis.exists(rate_key):
        ttl = redis.ttl(rate_key)
        raise AuthError(f"请求过于频繁，请 {max(ttl, 1)} 秒后再试")

    code = generate_verification_code()
    code_key = _email_code_key(email)
    try:
        redis.setex(code_key, settings.EMAIL_CODE_EXPIRE_SECONDS, code)
        redis.setex(rate_key, settings.EMAIL_CODE_RESEND_COOLDOWN, "1")
        logger.info("email code saved to redis key=%s ttl=%s", code_key, settings.EMAIL_CODE_EXPIRE_SECONDS)
    except Exception as exc:  # noqa: BLE001
        logger.exception("failed to write email code to redis for %s", email)
        raise AuthError("内部错误：无法保存验证码，请稍后重试") from exc

    try:
        await send_verification_email(to_email=email, code=code)
        logger.info("verification email sent (email=%s)", email)
    except EmailServiceError as exc:
        logger.error("email sending failed for %s, deleting redis key %s", email, code_key)
        try:
            redis.delete(code_key)
        except Exception:
            logger.exception("failed to delete redis code key after send failure: %s", code_key)
        raise


def verify_email_code(redis: Redis, email: str, code: str) -> None:
    email = email.strip().lower()
    stored = redis.get(_email_code_key(email))
    if stored is None:
        logger.info("verify email code failed: code missing for %s", email)
        raise AuthError("验证码已过期或不存在，请重新获取")
    if str(stored) != code.strip():
        logger.info("verify email code failed: code mismatch for %s", email)
        raise AuthError("验证码错误")


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> User | None:
    stmt = select(User).where(User.username == username.strip())
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email.strip().lower())
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_identifier(db: Session, identifier: str) -> User | None:
    value = identifier.strip()
    if "@" in value:
        return get_user_by_email(db, value.lower())
    return get_user_by_username(db, value)


def register_user(
    db: Session,
    redis: Redis,
    payload: RegisterRequest,
) -> UserPublic:
    verify_email_code(redis, payload.email, payload.code)

    if get_user_by_username(db, payload.username):
        logger.info("register failed: username exists %s", payload.username)
        raise AuthError("用户名已被注册")
    if get_user_by_email(db, payload.email):
        logger.info("register failed: email exists %s", payload.email)
        raise AuthError("邮箱已被注册")

    user = User(
        username=payload.username.strip(),
        email=payload.email.strip().lower(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    redis.delete(_email_code_key(payload.email))
    logger.info("user registered: id=%s username=%s", user.id, user.username)
    return UserPublic.model_validate(user)


def login_user(db: Session, payload: LoginRequest) -> tuple[str, UserPublic]:
    identifier = payload.username_or_email.strip()
    logger.info("login attempt identifier=%s", identifier)
    user = get_user_by_identifier(db, identifier)
    if user is None:
        logger.info("login user not found for identifier=%s", identifier)
        raise AuthError("用户名/邮箱或密码错误")

    logger.info("login user found: id=%s role=%s status=%s", user.id, user.role, user.status)
    password_ok = verify_password(payload.password, user.password_hash)
    logger.info("login password check result=%s for user_id=%s", password_ok, user.id)
    if not password_ok:
        raise AuthError("用户名/邮箱或密码错误")

    if getattr(user, "status", "active") == "disabled":
        raise AuthError("账号已被禁用")

    try:
        user.last_login_at = datetime.now(timezone.utc)
        db.add(user)
        db.commit()
    except Exception:
        logger.exception("failed to update last_login_at for user %s", user.id)
        db.rollback()

    token = create_access_token(str(user.id), extra={"username": user.username})
    logger.info("login success user_id=%s", user.id)
    return token, UserPublic.model_validate(user)


def list_users(db: Session, *, limit: int = 20) -> Sequence[User]:
    stmt = select(User).order_by(User.created_at.desc()).limit(limit)
    return db.execute(stmt).scalars().all()
