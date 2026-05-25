"""回测主循环。

每个交易日的处理顺序（保证不出现未来函数）：

    1. 读取策略给出的 ``signal[t]`` —— 按约定它仅基于 ``t-1`` 及更早数据
    2. **以 t 日 open 价**执行 BUY / SELL（提交订单需要时间，最早 t 日开盘成交）
    3. **以 t 日 close 价** mark-to-market，记录当日净值

输入是干净的 ``bars`` + ``signals``，输出是 ``trades`` 列表 + ``equity_curve`` 列表，
不接触数据库 / 网络，便于单测与并行运行。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence

import pandas as pd

from app.backtest.broker import Broker
from app.backtest.portfolio import Portfolio, Trade
from app.strategy.base import Signal


@dataclass
class EquityPoint:
    trade_date: date
    cash: float
    position: int
    close: float
    equity: float


def run_backtest(
    bars: pd.DataFrame,
    signals: pd.Series,
    portfolio: Portfolio,
    broker: Broker,
) -> tuple[list[Trade], list[EquityPoint]]:
    """执行回测并返回 (trades, equity_curve)。

    Args:
        bars: 至少含 ``trade_date`` / ``open`` / ``close`` 列，按 ``trade_date`` 升序。
        signals: 与 ``bars`` 同 index 的 :class:`Signal` 字符串序列。

    Raises:
        ValueError: bars 与 signals 长度不一致 / 缺列。
    """
    _validate_inputs(bars, signals)

    trades: list[Trade] = []
    equity_curve: list[EquityPoint] = []

    for i in range(len(bars)):
        row = bars.iloc[i]
        trade_date: date = _coerce_date(row["trade_date"])
        open_price = float(row["open"])
        close_price = float(row["close"])
        signal = signals.iloc[i]

        # ---- 1+2. 执行交易 -------------------------------------------
        trade: Trade | None = None
        if signal == Signal.BUY.value:
            trade = portfolio.buy_all(open_price, broker, trade_date, reason="MA 金叉")
        elif signal == Signal.SELL.value:
            trade = portfolio.sell_all(open_price, broker, trade_date, reason="MA 死叉")
        if trade is not None:
            trades.append(trade)

        # ---- 3. 记录净值（按 close 估值） -----------------------------
        equity_curve.append(
            EquityPoint(
                trade_date=trade_date,
                cash=portfolio.cash,
                position=portfolio.position,
                close=close_price,
                equity=portfolio.equity(close_price),
            )
        )

    return trades, equity_curve


# ---- 内部 ---------------------------------------------------------------

def _validate_inputs(bars: pd.DataFrame, signals: pd.Series) -> None:
    required = {"trade_date", "open", "close"}
    missing = required - set(bars.columns)
    if missing:
        raise ValueError(f"bars 缺列：{sorted(missing)}")
    if len(bars) != len(signals):
        raise ValueError(f"bars / signals 长度不一致：{len(bars)} vs {len(signals)}")


def _coerce_date(value: object) -> date:
    if isinstance(value, date) and not isinstance(value, pd.Timestamp):
        return value
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, str):
        return date.fromisoformat(value.replace("/", "-"))
    raise TypeError(f"unsupported trade_date type in bars: {type(value).__name__}")


__all__ = ["EquityPoint", "Trade", "run_backtest"]
