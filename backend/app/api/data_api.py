"""数据接入相关接口。"""

import logging
from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.stock_service import AkshareError, sync_daily_bars
from app.tasks import scheduler_state, trigger_watchlist_sync_now

logger = logging.getLogger("quant.api.data")

router = APIRouter(prefix="/data", tags=["data"])


# ---- Schemas ------------------------------------------------------------

class SyncDailyRequest(BaseModel):
    stock_code: str = Field(..., max_length=20, examples=["600519"])
    start_date: date = Field(..., examples=["2024-01-01"])
    end_date: date = Field(..., examples=["2024-01-31"])
    adjust: str = Field("", description='"" / "qfq" / "hfq"')


class SyncWatchlistRequest(BaseModel):
    stock_codes: list[str] | None = Field(
        default=None,
        description="不传则使用配置中的 WATCH_STOCKS",
        examples=[["600519", "000001"]],
    )


# ---- Routes -------------------------------------------------------------

@router.post("/sync", summary="触发数据同步（占位，统一入口）")
async def sync_data(
    target: str = Query("kline_daily", description="同步对象：kline_daily / basic / financial 等"),
) -> dict:
    return {"target": target, "status": "scheduled", "detail": "to be implemented"}


@router.post(
    "/sync/daily",
    summary="同步 A 股日线（akshare → MySQL）",
    description="从 akshare 拉取指定股票指定区间的日线数据，并 upsert 到 daily_bars 表。",
)
async def sync_stock_daily(
    payload: SyncDailyRequest = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    if payload.start_date > payload.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date 不能晚于 end_date",
        )

    try:
        return sync_daily_bars(
            db,
            payload.stock_code,
            payload.start_date,
            payload.end_date,
            adjust=payload.adjust,
        )
    except AkshareError as exc:
        logger.error("akshare sync failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"上游数据源失败：{exc}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/sync/status",
    summary="调度器状态与最近一次同步结果",
)
async def sync_status() -> dict:
    return {
        "scheduler_enabled": settings.SCHEDULER_ENABLED,
        "scheduler_running": scheduler_state.is_running,
        "timezone": settings.SCHEDULER_TIMEZONE,
        "schedule": {
            "hour": settings.SCHEDULER_DAILY_SYNC_HOUR,
            "minute": settings.SCHEDULER_DAILY_SYNC_MINUTE,
        },
        "watch_stocks": settings.watch_stocks_list,
        "jobs": scheduler_state.get_jobs_info(),
        "last_runs": scheduler_state.get_all_last_runs(),
    }


@router.post(
    "/sync/watchlist",
    summary="立即同步监控股票列表（不等定时任务）",
    description=(
        "对 `stock_codes`（不传则用配置中的 `WATCH_STOCKS`）拉取**今天**的日线"
        "并 upsert 到 daily_bars。结果会写入 `/sync/status` 的 `last_runs`。"
    ),
)
async def sync_watchlist_now(
    payload: SyncWatchlistRequest = Body(default_factory=SyncWatchlistRequest),
) -> dict:
    try:
        return trigger_watchlist_sync_now(payload.stock_codes)
    except Exception as exc:  # noqa: BLE001
        logger.exception("watchlist sync trigger failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"watchlist 同步失败：{exc}",
        ) from exc


@router.get("/kline/{code}", summary="获取 K 线（占位，建议改用 /stocks/{code}/daily）")
async def get_kline(
    code: str,
    period: str = Query("daily", pattern="^(daily|weekly|monthly|60min|30min|15min|5min|1min)$"),
    start: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    end: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
) -> dict:
    return {
        "code": code,
        "period": period,
        "start": start,
        "end": end,
        "items": [],
        "detail": "to be implemented; use /stocks/{code}/daily for now",
    }
