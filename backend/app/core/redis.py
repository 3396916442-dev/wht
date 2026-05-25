"""Redis 客户端管理。

模块级单例 + FastAPI 依赖：
    - ``get_redis_client()`` 拿到底层 redis-py 客户端（线程安全）
    - ``get_redis``           作为 FastAPI ``Depends`` 使用
    - ``close_redis_client()``在 lifespan 中释放连接
    - ``ping_redis()``        探活
"""

from typing import Optional

from redis import Redis

from app.core.config import settings


_client: Optional[Redis] = None


def get_redis_client() -> Redis:
    """惰性创建模块级 Redis 客户端。"""
    global _client
    if _client is None:
        _client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
    return _client


def get_redis() -> Redis:
    """FastAPI 依赖注入入口。"""
    return get_redis_client()


def ping_redis() -> bool:
    """探活：``PING`` 一次。失败抛出原始异常。"""
    return bool(get_redis_client().ping())


def close_redis_client() -> None:
    global _client
    if _client is not None:
        try:
            _client.close()
        finally:
            _client = None
