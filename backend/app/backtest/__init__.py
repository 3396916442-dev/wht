"""回测引擎（自研轻量版）。

模块职责：
    - :mod:`broker`      费率 / 滑点 / 印花税
    - :mod:`portfolio`   资金 + 持仓状态机
    - :mod:`engine`      主循环，输入 bars + signals → trades + equity_curve
    - :mod:`performance` 净值 → 绩效指标

后期保留 ``adapters/backtrader_adapter.py``，将本平台 ``Strategy``
适配到 Backtrader 上，复用其成熟生态。
"""

from app.backtest.broker import Broker
from app.backtest.engine import EquityPoint, Trade, run_backtest
from app.backtest.performance import compute_metrics
from app.backtest.portfolio import LOT_SIZE, Portfolio

__all__ = [
    "Broker",
    "Portfolio",
    "Trade",
    "EquityPoint",
    "run_backtest",
    "compute_metrics",
    "LOT_SIZE",
]
