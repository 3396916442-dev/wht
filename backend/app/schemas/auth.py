"""认证相关 Pydantic 模型。"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


QQ_EMAIL_PATTERN = re.compile(r"^[1-9]\d{4,10}@qq\.com$", re.IGNORECASE)


class SendCodeRequest(BaseModel):
    email: EmailStr = Field(..., examples=["123456789@qq.com"])

    @field_validator("email")
    @classmethod
    def validate_qq_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not QQ_EMAIL_PATTERN.match(email):
            raise ValueError("仅支持 QQ 邮箱，格式如 123456789@qq.com")
        return email


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32, examples=["quant_user"])
    password: str = Field(..., min_length=8, max_length=128)
    email: EmailStr = Field(..., examples=["123456789@qq.com"])
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        username = value.strip()
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            raise ValueError("用户名只能包含字母、数字和下划线")
        return username

    @field_validator("email")
    @classmethod
    def validate_qq_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not QQ_EMAIL_PATTERN.match(email):
            raise ValueError("仅支持 QQ 邮箱，格式如 123456789@qq.com")
        return email

class LoginRequest(BaseModel):
    username_or_email: str = Field(
        ..., min_length=3, max_length=100, description="用户名或邮箱"
    )
    password: str = Field(..., min_length=8, max_length=128)


class UserPublic(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: Literal["user", "admin", "super_admin"]
    status: Literal["active", "disabled"]
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class MessageResponse(BaseModel):
    message: str
