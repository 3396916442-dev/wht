"""ORM 模型层。

通过显式 import 把所有模型注册到 ``Base.metadata``，
``init_db.create_all`` 与未来的 Alembic ``autogenerate`` 都依赖这里的 import 副作用。
"""

from app.core.database import Base
from app.models.backtest import (
    BacktestResult,
    BacktestStatus,
    BacktestTask,
    BacktestTrade,
    TradeAction,
)
from app.models.kline import DailyBar
from app.models.stock import StockBasic
from app.models.strategy import Strategy
from app.models.user import User

__all__ = [
    "Base",
    "StockBasic",
    "DailyBar",
    "Strategy",
    "BacktestTask",
    "BacktestResult",
    "BacktestTrade",
    "BacktestStatus",
    "TradeAction",
    "User",
]
