"""APScheduler 全局调度器。

第一版只注册一个 cron 任务：
    - ``watchlist_daily_sync`` —— 每天 ``settings.SCHEDULER_DAILY_SYNC_HOUR:MINUTE``
      触发 :func:`sync_watchlist_daily`，按 ``settings.WATCH_STOCKS`` 拉当日日线。

线程模型
========
- ``BackgroundScheduler`` 把 job 派到独立工作线程
- Job 内部自创 ``SessionLocal()``，不依赖 FastAPI 的 ``get_db``
- :class:`SchedulerState` 用 ``threading.Lock`` 保护可变字段

==========================================
后期切换到 Celery 的指引（**第一版不实现**）
==========================================

切到 Celery 的最小改动路径：

    1. 新增 ``app/tasks/celery_app.py``，暴露 ``celery_app = Celery(...)``。
    2. 在 :mod:`sync_daily_data` 中给 ``sync_watchlist_daily`` 加 ``@celery_app.task`` 装饰器，
       使其同时可作为 APScheduler 函数与 Celery task。
    3. 用独立的 ``celery worker`` + ``celery beat`` 进程替代本模块的
       ``BackgroundScheduler``；不要再在 FastAPI lifespan 里启动调度器。
    4. 把 :class:`SchedulerState` 的"最近运行结果"换成 Redis（多进程共享），
       本平台已自带 Redis 客户端，无需新依赖。

调度器接口（``start_scheduler`` / ``shutdown_scheduler`` /
``trigger_watchlist_sync_now`` / ``SchedulerState``）保持不变即可。
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.tasks.sync_daily_data import sync_watchlist_daily

logger = logging.getLogger("quant.scheduler")


# Job ID 常量（升级 Celery 时复用为 task name）
JOB_DAILY_SYNC = "watchlist_daily_sync"


# ---- 状态对象 -----------------------------------------------------------

class SchedulerState:
    """调度器运行时状态。

    内存级，进程重启即丢失（持久化历史运行记录是后续工作，建议建 ``task_runs`` 表
    或写入 Redis Stream / List）。
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._scheduler: BackgroundScheduler | None = None
        self._last_run: dict[str, dict[str, Any]] = {}

    @property
    def is_running(self) -> bool:
        return self._scheduler is not None and self._scheduler.running

    def get_scheduler(self) -> BackgroundScheduler | None:
        return self._scheduler

    def _set_scheduler(self, scheduler: BackgroundScheduler | None) -> None:
        with self._lock:
            self._scheduler = scheduler

    def record_run(self, job_id: str, result: dict[str, Any]) -> None:
        with self._lock:
            self._last_run[job_id] = result

    def get_last_run(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._last_run.get(job_id)

    def get_all_last_runs(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return dict(self._last_run)

    def get_jobs_info(self) -> list[dict[str, Any]]:
        sch = self._scheduler
        if sch is None or not sch.running:
            return []
        out: list[dict[str, Any]] = []
        for job in sch.get_jobs():
            out.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "trigger": str(job.trigger),
                    "next_run_time": (
                        job.next_run_time.isoformat() if job.next_run_time else None
                    ),
                }
            )
        return out


# 模块级单例
state = SchedulerState()


# ---- Job 包装：执行 + 记录结果 + 永不抛异常 ----------------------------

def _run_watchlist_sync_with_record(triggered_by: str = "schedule") -> dict[str, Any]:
    """调度器 / 手动触发都通过这里调用，统一记录状态。"""
    try:
        result = sync_watchlist_daily()
        result["status"] = "success" if result.get("failed", 0) == 0 else "partial"
        result["triggered_by"] = triggered_by
        state.record_run(JOB_DAILY_SYNC, result)
        return result
    except Exception as exc:  # noqa: BLE001 - 防止异常逃逸到 BackgroundScheduler
        logger.exception("watchlist daily sync crashed")
        record: dict[str, Any] = {
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "finished_at": datetime.now().isoformat(timespec="seconds"),
            "triggered_by": triggered_by,
        }
        state.record_run(JOB_DAILY_SYNC, record)
        return record


def trigger_watchlist_sync_now(stock_codes: list[str] | None = None) -> dict[str, Any]:
    """立即同步（``POST /sync/watchlist`` 用）。

    与定时任务共用同一状态槽位 ``JOB_DAILY_SYNC``，结果会出现在 ``/sync/status``。
    """
    if stock_codes is not None:
        # 显式指定 stock_codes 的路径走得更直接（不用经过 _run 包装的统一 job）
        logger.info("manual watchlist sync: codes=%s", stock_codes)
        try:
            result = sync_watchlist_daily(stock_codes=stock_codes)
            result["status"] = "success" if result.get("failed", 0) == 0 else "partial"
            result["triggered_by"] = "manual"
            state.record_run(JOB_DAILY_SYNC, result)
            return result
        except Exception as exc:
            logger.exception("manual watchlist sync crashed")
            record = {
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "finished_at": datetime.now().isoformat(timespec="seconds"),
                "triggered_by": "manual",
            }
            state.record_run(JOB_DAILY_SYNC, record)
            return record
    return _run_watchlist_sync_with_record(triggered_by="manual")


# ---- 启停（幂等） ------------------------------------------------------

def start_scheduler() -> BackgroundScheduler | None:
    """初始化并启动 BackgroundScheduler。

    幂等：重复调用直接返回当前实例。
    ``settings.SCHEDULER_ENABLED=False`` 时返回 ``None``（用于测试 / 单纯跑后端 API）。
    """
    if not settings.SCHEDULER_ENABLED:
        logger.info("scheduler disabled by settings.SCHEDULER_ENABLED=False")
        return None

    if state.is_running:
        logger.debug("scheduler already running, skip start")
        return state.get_scheduler()

    scheduler = BackgroundScheduler(timezone=settings.SCHEDULER_TIMEZONE)
    scheduler.add_job(
        _run_watchlist_sync_with_record,
        trigger=CronTrigger(
            hour=settings.SCHEDULER_DAILY_SYNC_HOUR,
            minute=settings.SCHEDULER_DAILY_SYNC_MINUTE,
            timezone=settings.SCHEDULER_TIMEZONE,
        ),
        id=JOB_DAILY_SYNC,
        name="watchlist daily sync",
        replace_existing=True,
        misfire_grace_time=3600,  # 1 小时内补跑一次
        max_instances=1,
    )

    scheduler.start()
    state._set_scheduler(scheduler)

    logger.info(
        "scheduler started: %s daily at %02d:%02d %s, watch=%s",
        JOB_DAILY_SYNC,
        settings.SCHEDULER_DAILY_SYNC_HOUR,
        settings.SCHEDULER_DAILY_SYNC_MINUTE,
        settings.SCHEDULER_TIMEZONE,
        settings.watch_stocks_list,
    )
    return scheduler


def shutdown_scheduler() -> None:
    """关闭调度器；不等当前 job 完成（避免阻塞 FastAPI 关闭）。"""
    sch = state.get_scheduler()
    if sch is not None and sch.running:
        sch.shutdown(wait=False)
        logger.info("scheduler shutdown (wait=False)")
    state._set_scheduler(None)


__all__ = [
    "JOB_DAILY_SYNC",
    "SchedulerState",
    "state",
    "start_scheduler",
    "shutdown_scheduler",
    "trigger_watchlist_sync_now",
]
