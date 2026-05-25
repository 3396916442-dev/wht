"""开发期迁移：为 users 表补充管理员字段。

用法：
    cd backend && python -m app.scripts.upgrade_users_table
"""

from __future__ import annotations

import logging

from sqlalchemy import text

from app.core.database import engine
from app.core.config import settings

logger = logging.getLogger("quant.upgrade_users_table")


def column_exists(column_name: str) -> bool:
    query = text(
        """
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_schema = :schema
          AND table_name = 'users'
          AND column_name = :column
        """
    )
    with engine.connect() as conn:
        result = conn.execute(
            query,
            {"schema": settings.MYSQL_DATABASE, "column": column_name},
        )
        return int(result.scalar_one()) > 0


def add_column(sql: str) -> None:
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    additions = []
    if not column_exists("role"):
        additions.append("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '角色: user/admin/super_admin'")
    if not column_exists("status"):
        additions.append("ALTER TABLE users ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态: active/disabled'")
    if not column_exists("updated_at"):
        additions.append(
            "ALTER TABLE users ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        )
    if not column_exists("last_login_at"):
        additions.append("ALTER TABLE users ADD COLUMN last_login_at DATETIME NULL")

    if not additions:
        logger.info("users table already up to date")
        return

    for stmt in additions:
        logger.info("executing: %s", stmt)
        add_column(stmt)

    logger.info("users table upgrade complete")


if __name__ == "__main__":
    main()
