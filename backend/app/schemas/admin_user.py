"""管理员用户管理相关 Schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

UserRole = Literal["user", "admin", "super_admin"]
UserStatus = Literal["active", "disabled"]


class AdminUserListItem(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    status: UserStatus
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = {"from_attributes": True}


class AdminUserDetail(AdminUserListItem):
    updated_at: datetime


class AdminUserListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminUserListItem]


class AdminUserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    status: UserStatus | None = None
    role: UserRole | None = None


class AdminPasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)
