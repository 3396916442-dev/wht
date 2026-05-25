"""创建超级管理员（开发环境使用）。

用法：
    cd backend && python scripts/create_super_admin.py

环境变量：
    ADMIN_USERNAME=admin
    ADMIN_PASSWORD=change_me_to_strong_password
    ADMIN_EMAIL=admin@qq.com
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy import inspect, select
from sqlalchemy.exc import SQLAlchemyError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import models  # noqa: F401  - 注册模型
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.models.user import User

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change_me_to_strong_password")

REQUIRED_USER_COLUMNS = {
    "id",
    "username",
    "email",
    "password_hash",
    "role",
    "status",
    "created_at",
    "updated_at",
    "last_login_at",
}

MISSING_COLUMN_SQL = {
    "role": "ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '角色: user/admin/super_admin';",
    "status": "ALTER TABLE users ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态: active/disabled';",
    "updated_at": "ALTER TABLE users ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;",
    "last_login_at": "ALTER TABLE users ADD COLUMN last_login_at DATETIME NULL;",
}


def check_users_table() -> bool:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        print("失败：users 表不存在。请先执行：python -m app.scripts.init_db")
        return False

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    missing = sorted(REQUIRED_USER_COLUMNS - existing_columns)
    if not missing:
        return True

    print("失败：users 表缺少字段：%s" % ", ".join(missing))
    print("可执行以下开发环境迁移命令：python -m app.scripts.upgrade_users_table")
    print("或手动执行以下 ALTER TABLE SQL：")
    for column in missing:
        print(MISSING_COLUMN_SQL.get(column, f"-- 请为 users 表补充字段：{column}"))
    return False


def main() -> None:
    username = settings.ADMIN_USERNAME.strip()
    password = ADMIN_PASSWORD.strip()
    email = settings.ADMIN_EMAIL.strip().lower()

    if not username or not password or not email:
        print("失败：ADMIN_USERNAME/ADMIN_PASSWORD/ADMIN_EMAIL 不能为空")
        raise SystemExit(1)

    try:
        if not check_users_table():
            raise SystemExit(1)
    except SQLAlchemyError as exc:
        print(f"失败：检查 users 表失败：{exc}")
        raise SystemExit(1) from exc

    session = SessionLocal()
    try:
        existing = session.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()

        if existing is None:
            email_owner = session.execute(
                select(User).where(User.email == email)
            ).scalar_one_or_none()
            if email_owner is not None:
                print(
                    "失败：ADMIN_EMAIL 已被其他用户占用："
                    f"user_id={email_owner.id} username={email_owner.username}"
                )
                raise SystemExit(1)

            user = User(
                username=username,
                email=email,
                password_hash=hash_password(password),
                role="super_admin",
                status="active",
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            print(f"创建成功：id={user.id} username={user.username} role={user.role} status={user.status}")
            return

        changed = False
        if existing.role != "super_admin":
            existing.role = "super_admin"
            changed = True
        if existing.status != "active":
            existing.status = "active"
            changed = True

        if changed:
            session.add(existing)
            session.commit()
            session.refresh(existing)
        else:
            session.rollback()

        print(
            "已存在并已确认权限："
            f"id={existing.id} username={existing.username} role={existing.role} status={existing.status}"
        )
    except SQLAlchemyError as exc:
        session.rollback()
        print(f"失败：创建或更新超级管理员失败：{exc}")
        raise SystemExit(1) from exc
    finally:
        session.close()


if __name__ == "__main__":
    main()
