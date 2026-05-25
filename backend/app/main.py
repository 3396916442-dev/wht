"""FastAPI 应用入口。

职责：
    - 初始化日志
    - 在 lifespan 中检查 MySQL / Redis 连接（连不上仅日志告警，不阻断启动）
    - 装载 CORS
    - 注册根级 /health 与 /api/v1/* 业务路由
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.api.auth import router as auth_router
from app.api.admin_user import router as admin_user_router
from app.core.config import settings
from app.core.database import dispose_engine, ping_db
from app.core.redis import close_redis_client, ping_redis
from app.tasks import shutdown_scheduler, start_scheduler


logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("quant.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting %s v%s", settings.PROJECT_NAME, settings.VERSION)

    try:
        ping_db()
        logger.info(
            "MySQL connected: %s:%s/%s",
            settings.MYSQL_HOST,
            settings.MYSQL_PORT,
            settings.MYSQL_DATABASE,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("MySQL not reachable on startup: %s", exc)

    try:
        ping_redis()
        logger.info("Redis connected: %s:%s/%s", settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_DB)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis not reachable on startup: %s", exc)

    try:
        start_scheduler()
    except Exception as exc:  # noqa: BLE001 - 调度器失败不应阻断 API
        logger.warning("scheduler start failed: %s", exc)

    yield

    # 关闭顺序：先停调度器（避免新 job 用到已 dispose 的连接池），再放资源
    try:
        shutdown_scheduler()
    except Exception:  # noqa: BLE001
        logger.exception("scheduler shutdown error (ignored)")
    close_redis_client()
    dispose_engine()
    logger.info("shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="A 股量化交易分析平台 后端服务",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled API error: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "内部服务器错误，请检查后端日志或依赖服务状态"},
    )

app.include_router(api_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix="/api")
app.include_router(admin_user_router, prefix="/api")


@app.get("/", tags=["meta"], summary="服务元信息")
async def root() -> dict:
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "api": settings.API_PREFIX,
    }


@app.get("/health", tags=["meta"], summary="健康检查（含依赖探活）")
async def health() -> dict:
    """轻量健康检查：自身始终 OK，附带 MySQL/Redis 连通性供观察。"""
    mysql_ok = False
    redis_ok = False
    try:
        ping_db()
        mysql_ok = True
    except Exception as exc:  # noqa: BLE001
        logger.debug("health: mysql ping failed: %s", exc)
    try:
        ping_redis()
        redis_ok = True
    except Exception as exc:  # noqa: BLE001
        logger.debug("health: redis ping failed: %s", exc)

    return {
        "status": "ok",
        "version": settings.VERSION,
        "checks": {"mysql": mysql_ok, "redis": redis_ok},
    }
