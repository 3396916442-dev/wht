"""管理员用户管理 API。"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin, require_super_admin
from app.core.security import hash_password
from app.models.user import User
from app.schemas.admin_user import (
    AdminPasswordResetRequest,
    AdminUserDetail,
    AdminUserListResponse,
    AdminUserListItem,
    AdminUserUpdate,
)

logger = logging.getLogger("quant.api.admin.users")

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


def _count_active_super_admins(db: Session) -> int:
    stmt = select(func.count()).select_from(User).where(
        User.role == "super_admin", User.status == "active"
    )
    return int(db.execute(stmt).scalar_one())


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return user


@router.get("", summary="用户列表", response_model=AdminUserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    role: str | None = None,
    status: str | None = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminUserListResponse:
    stmt = select(User)
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(or_(User.username.like(like), User.email.like(like)))
    if role:
        stmt = stmt.where(User.role == role)
    if status:
        stmt = stmt.where(User.status == status)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = (
        db.execute(
            stmt.order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return AdminUserListResponse(
        total=int(total),
        page=page,
        page_size=page_size,
        items=[AdminUserListItem.model_validate(u) for u in items],
    )


@router.get("/{user_id}", summary="用户详情", response_model=AdminUserDetail)
def get_user_detail(
    user_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminUserDetail:
    user = _get_user_or_404(db, user_id)
    return AdminUserDetail.model_validate(user)


@router.put("/{user_id}", summary="更新用户信息", response_model=AdminUserDetail)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminUserDetail:
    user = _get_user_or_404(db, user_id)

    if current_user.role != "super_admin" and user.role == "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限修改超级管理员")

    if payload.role is not None and current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有超级管理员可修改角色")

    if payload.role is not None and user.role == "super_admin" and payload.role != "super_admin":
        if _count_active_super_admins(db) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能降级最后一个超级管理员",
            )

    if payload.status is not None and user.role == "super_admin" and payload.status != "active":
        if _count_active_super_admins(db) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能禁用最后一个超级管理员",
            )

    if payload.username is not None:
        user.username = payload.username.strip()
    if payload.email is not None:
        user.email = payload.email.strip().lower()
    if payload.status is not None:
        user.status = payload.status
    if payload.role is not None:
        user.role = payload.role

    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("user updated: id=%s by=%s", user.id, current_user.id)
    return AdminUserDetail.model_validate(user)


@router.delete("/{user_id}", summary="删除用户")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> dict:
    if current_user.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除自己")

    user = _get_user_or_404(db, user_id)
    if user.role == "super_admin" and _count_active_super_admins(db) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除最后一个超级管理员",
        )

    db.delete(user)
    db.commit()
    logger.info("user deleted: id=%s by=%s", user_id, current_user.id)
    return {"message": "ok"}


@router.post("/{user_id}/reset-password", summary="重置用户密码")
def reset_password(
    user_id: int,
    payload: AdminPasswordResetRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    user = _get_user_or_404(db, user_id)
    if current_user.role != "super_admin" and user.role == "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="不能重置超级管理员密码")

    user.password_hash = hash_password(payload.new_password)
    db.add(user)
    db.commit()
    logger.info("user password reset: id=%s by=%s", user_id, current_user.id)
    return {"message": "ok"}
