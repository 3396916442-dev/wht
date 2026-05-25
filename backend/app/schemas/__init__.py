"""Pydantic 数据契约（与 ORM 模型一一对应）。"""

from app.schemas.backtest import (
    BacktestResultBase,
    BacktestResultCreate,
    BacktestResultRead,
    BacktestTaskBase,
    BacktestTaskCreate,
    BacktestTaskRead,
    BacktestTaskUpdate,
    BacktestTradeBase,
    BacktestTradeCreate,
    BacktestTradeRead,
)
from app.schemas.kline import DailyBarBase, DailyBarCreate, DailyBarRead
from app.schemas.stock import (
    StockBasicBase,
    StockBasicCreate,
    StockBasicRead,
    StockBasicUpdate,
)
from app.schemas.strategy import (
    StrategyBase,
    StrategyCreate,
    StrategyRead,
    StrategyUpdate,
)

__all__ = [
    # stock
    "StockBasicBase",
    "StockBasicCreate",
    "StockBasicUpdate",
    "StockBasicRead",
    # kline
    "DailyBarBase",
    "DailyBarCreate",
    "DailyBarRead",
    # strategy
    "StrategyBase",
    "StrategyCreate",
    "StrategyUpdate",
    "StrategyRead",
    # backtest
    "BacktestTaskBase",
    "BacktestTaskCreate",
    "BacktestTaskUpdate",
    "BacktestTaskRead",
    "BacktestResultBase",
    "BacktestResultCreate",
    "BacktestResultRead",
    "BacktestTradeBase",
    "BacktestTradeCreate",
    "BacktestTradeRead",
]
