"""任务调度层（第一版 APScheduler）。

模块布局：
    - :mod:`scheduler`        全局 BackgroundScheduler + SchedulerState
    - :mod:`sync_daily_data`  每日 watchlist 行情同步任务（业务实现）

后期切换到 Celery 的指引在 :mod:`scheduler` 顶部 docstring。
"""

from app.tasks.scheduler import (
    JOB_DAILY_SYNC,
    SchedulerState,
    shutdown_scheduler,
    start_scheduler,
    state as scheduler_state,
    trigger_watchlist_sync_now,
)
from app.tasks.sync_daily_data import sync_watchlist_daily

__all__ = [
    "JOB_DAILY_SYNC",
    "SchedulerState",
    "scheduler_state",
    "start_scheduler",
    "shutdown_scheduler",
    "trigger_watchlist_sync_now",
    "sync_watchlist_daily",
]
