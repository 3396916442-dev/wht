"""QQ 邮箱 SMTP 发送服务。"""

from __future__ import annotations

import logging
from email.message import EmailMessage
import smtplib
import ssl
import asyncio

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger("quant.email")


class EmailServiceError(RuntimeError):
    """邮件发送失败。"""


def _sync_send_via_smtp_ssl(message: EmailMessage, host: str, port: int, username: str, password: str, timeout: int = 15) -> None:
    """同步通过 smtplib.SMTP_SSL 发送邮件（用于在异步发送失败时回退）。"""
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=context, timeout=timeout) as server:
        server.login(username, password)
        server.send_message(message)


async def send_verification_email(*, to_email: str, code: str) -> None:
    """通过 QQ SMTP（SSL 465）发送 6 位验证码。优先尝试 aiosmtplib，失败后回退到 smtplib.SMTP_SSL。"""
    if not settings.QQ_EMAIL or not settings.QQ_EMAIL_AUTH_CODE:
        raise EmailServiceError(
            "邮件服务未配置，请在 backend/.env 设置 QQ_EMAIL 与 QQ_EMAIL_AUTH_CODE"
        )

    message = EmailMessage()
    message["From"] = settings.QQ_EMAIL
    message["To"] = to_email
    message["Subject"] = f"【{settings.PROJECT_NAME}】邮箱验证码"
    message.set_content(
        f"您的验证码是：{code}\n\n"
        f"验证码 {settings.EMAIL_CODE_EXPIRE_SECONDS // 60} 分钟内有效，请勿泄露。\n"
        f"如非本人操作，请忽略此邮件。"
    )

    # First try aiosmtplib (async)
    try:
        await aiosmtplib.send(
            message,
            hostname=settings.QQ_SMTP_HOST,
            port=settings.QQ_SMTP_PORT,
            use_tls=True,
            username=settings.QQ_EMAIL,
            password=settings.QQ_EMAIL_AUTH_CODE,
            timeout=15,
        )
        logger.info("verification email sent to %s via aiosmtplib", to_email)
        return
    except Exception as exc:  # noqa: BLE001
        logger.warning("aiosmtplib send failed for %s: %s, attempting sync fallback", to_email, exc)

    # Fallback to synchronous smtplib in a thread to avoid blocking event loop
    try:
        await asyncio.to_thread(
            _sync_send_via_smtp_ssl,
            message,
            settings.QQ_SMTP_HOST,
            settings.QQ_SMTP_PORT,
            settings.QQ_EMAIL,
            settings.QQ_EMAIL_AUTH_CODE,
            15,
        )
        logger.info("verification email sent to %s via smtplib.SMTP_SSL fallback", to_email)
        return
    except Exception as exc:  # noqa: BLE001
        logger.exception("fallback smtplib send failed for %s", to_email)
        raise EmailServiceError(f"验证码邮件发送失败：{exc}") from exc
