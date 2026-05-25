"""业务服务层。

每个领域提供一个服务实例，API 层 / 任务层直接 import 使用：

    from app.services import stock_service, daily_bar_service
"""

from app.services.backtest_service import (
    backtest_result_service,
    backtest_task_service,
    backtest_trade_service,
)
from app.services.crud_base import CRUDBase
from app.services.kline_service import daily_bar_service
from app.services.stock_service import stock_service
from app.services.strategy_service import strategy_service

__all__ = [
    "CRUDBase",
    "stock_service",
    "daily_bar_service",
    "strategy_service",
    "backtest_task_service",
    "backtest_result_service",
    "backtest_trade_service",
]
