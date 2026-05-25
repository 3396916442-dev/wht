"""认证 API：验证码 / 注册 / 登录 / 当前用户。"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from redis import Redis
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.redis import get_redis
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RegisterRequest,
    SendCodeRequest,
    UserPublic,
)
from app.services.auth_service import AuthError, login_user, register_user, send_email_code
from app.services.email_service import EmailServiceError
from app.core.config import settings

logger = logging.getLogger("quant.api.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/send-code",
    summary="发送 QQ 邮箱验证码",
    response_model=MessageResponse,
)
async def send_code(
    payload: SendCodeRequest,
    redis: Redis = Depends(get_redis),
) -> MessageResponse:
    logger.info("send-code request received for email=%s", payload.email)
    # log whether SMTP config exists (do not log secrets)
    logger.info(
        "smtp config: host=%s port=%s ssl=%s configured_email=%s",
        settings.QQ_SMTP_HOST,
        settings.QQ_SMTP_PORT,
        True,
        bool(settings.QQ_EMAIL),
    )
    try:
        await send_email_code(redis, payload.email)
        logger.info("verification code workflow finished for %s", payload.email)
        return MessageResponse(message="验证码已发送，请查收 QQ 邮箱")
    except AuthError as exc:
        logger.warning("send-code rate/auth error for %s: %s", payload.email, exc)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except EmailServiceError as exc:
        logger.error("send-code email service failed for %s: %s", payload.email, exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - unexpected
        logger.exception("unexpected error in send-code for %s", payload.email)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="内部服务器错误，发送失败") from exc


@router.post(
    "/register",
    summary="用户注册",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> UserPublic:
    try:
        logger.info("register request received: username=%s email=%s", payload.username, payload.email)
        return register_user(db, redis, payload)
    except AuthError as exc:
        logger.warning("register failed for %s: %s", payload.email, exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/login",
    summary="用户登录",
    response_model=LoginResponse,
)
async def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    try:
        logger.info("login request received: identifier=%s", payload.username_or_email)
        token, user = login_user(db, payload)
        return LoginResponse(access_token=token, user=user)
    except AuthError as exc:
        logger.warning("login failed for identifier=%s: %s", payload.username_or_email, exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get(
    "/me",
    summary="获取当前登录用户信息",
    response_model=UserPublic,
)
async def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(current_user)
