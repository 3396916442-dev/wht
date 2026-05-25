"""SQLAlchemy 引擎与会话工厂。

对外暴露：
    - ``engine``        ：全局共享引擎
    - ``SessionLocal``  ：会话工厂
    - ``Base``          ：所有 ORM 模型的基类
    - ``get_db``        ：FastAPI 依赖注入
    - ``ping_db``       ：lifespan / 健康检查使用
    - ``dispose_engine``：lifespan 关闭时释放连接
"""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=settings.MYSQL_POOL_SIZE,
    pool_recycle=settings.MYSQL_POOL_RECYCLE,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：注入一个数据库会话，请求结束自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ping_db() -> bool:
    """探活：执行一次 ``SELECT 1`` 验证连接。失败抛出原始异常。"""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True


def dispose_engine() -> None:
    """关闭所有连接（用于 lifespan 收尾）。"""
    engine.dispose()
