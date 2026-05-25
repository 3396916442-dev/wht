"""每日行情同步任务（业务实现）。

第一版策略：对 ``settings.WATCH_STOCKS`` 列出的所有股票，拉取**指定日期**
的日线数据并 ``upsert`` 到 ``daily_bars``。

设计要点：
    - **单只失败不影响其它**：每只股票独立 try/except，错误转成结果项
    - **自管 SessionLocal**：调度器后台线程触发时不依赖 FastAPI 的 ``get_db``
    - **节假日不特殊处理**：直接交给 akshare（非交易日返回空，``fetched=0``）
    - **状态结构化**：返回的 dict 可直接被 :class:`SchedulerState` 缓存供 API 查询
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.stock_service import AkshareError, sync_daily_bars

logger = logging.getLogger("quant.tasks.sync_daily")


def sync_watchlist_daily(
    stock_codes: list[str] | None = None,
    target_date: date | None = None,
) -> dict[str, Any]:
    """同步监控列表的指定日期日线。

    Args:
        stock_codes: 默认 ``settings.watch_stocks_list``。
        target_date: 默认 ``date.today()``。

    Returns:
        汇总结构（JSON-friendly），形如::

            {
                "started_at": ISO,
                "finished_at": ISO,
                "duration_seconds": 12.34,
                "target_date": "2026-05-23",
                "total": 3,
                "success": 2,
                "failed": 1,
                "per_stock": [
                    {"stock_code": "600519", "status": "success",
                     "fetched": 1, "saved": {"total": 1, "affected": 1}},
                    {"stock_code": "000001", "status": "failed",
                     "error": "akshare 调用失败：..."},
                    ...
                ],
            }
    """
    codes = stock_codes if stock_codes is not None else settings.watch_stocks_list
    target = target_date or date.today()

    started_at = datetime.now()
    logger.info(
        "watchlist daily sync start: codes=%s target=%s",
        codes, target.isoformat(),
    )

    per_stock: list[dict[str, Any]] = []
    success = 0
    failed = 0

    db = SessionLocal()
    try:
        for code in codes:
            try:
                result = sync_daily_bars(db, code, target, target)
                per_stock.append(
                    {
                        "stock_code": code,
                        "status": "success",
                        "fetched": result["fetched"],
                        "saved": result["saved"],
                    }
                )
                success += 1
            except AkshareError as exc:
                logger.warning("sync %s failed (akshare): %s", code, exc)
                per_stock.append(
                    {"stock_code": code, "status": "failed", "error": str(exc)}
                )
                failed += 1
            except Exception as exc:  # noqa: BLE001 - 单只兜底
                logger.exception("sync %s failed (unexpected): %s", code, exc)
                per_stock.append(
                    {
                        "stock_code": code,
                        "status": "failed",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                failed += 1
    finally:
        db.close()

    finished_at = datetime.now()
    summary: dict[str, Any] = {
        "started_at": started_at.isoformat(timespec="seconds"),
        "finished_at": finished_at.isoformat(timespec="seconds"),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
        "target_date": target.isoformat(),
        "total": len(codes),
        "success": success,
        "failed": failed,
        "per_stock": per_stock,
    }
    logger.info(
        "watchlist daily sync done: %s/%s success in %.2fs",
        success, len(codes), summary["duration_seconds"],
    )
    return summary
