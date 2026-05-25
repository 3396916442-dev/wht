"""一键建表脚本（第一版不使用 Alembic）。

用法：
    # docker compose 模式
    docker compose exec backend python -m app.scripts.init_db
    docker compose exec backend python -m app.scripts.init_db --drop  # 慎用

    # 本机直跑
    cd backend && python -m app.scripts.init_db

未来切换到 Alembic 时，本脚本可保留作为开发期"快速重置"工具。
"""

from __future__ import annotations

import argparse
import logging

from app import models  # noqa: F401  - 触发模型注册到 metadata
from app.core.database import Base, engine

logger = logging.getLogger("quant.init_db")


def create_all() -> list[str]:
    Base.metadata.create_all(bind=engine)
    return sorted(Base.metadata.tables.keys())


def drop_all() -> list[str]:
    tables = sorted(Base.metadata.tables.keys())
    Base.metadata.drop_all(bind=engine)
    return tables


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化 / 重置数据库")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="先 drop 再 create（开发期重置数据库时使用，会丢失全部数据）",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if args.drop:
        logger.warning("DROP all tables ...")
        dropped = drop_all()
        logger.warning("dropped: %s", dropped)

    logger.info("CREATE all tables ...")
    created = create_all()
    logger.info("done. tables: %s", created)


if __name__ == "__main__":
    main()
