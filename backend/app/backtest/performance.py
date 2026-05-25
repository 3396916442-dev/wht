"""绩效指标计算。

输入完全是 ``run_backtest`` 的输出，不接触数据库。

约定：
    - 默认 ``trading_days_per_year = 252``
    - 无风险利率 ``rf = 0``
    - 一对成对 BUY → SELL 算一笔"完整交易"，``win_rate`` 基于完整交易
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from app.backtest.engine import EquityPoint
from app.backtest.portfolio import Trade

TRADING_DAYS_PER_YEAR = 252


def _safe_float(value: float | None) -> float | None:
    if value is None:
        return None
    if not np.isfinite(value):
        return None
    return float(value)


def compute_metrics(
    equity_curve: Sequence[EquityPoint],
    trades: Sequence[Trade],
) -> dict[str, float | int | None]:
    """计算总收益 / 年化 / 最大回撤 / 夏普 / 胜率 / 交易次数。

    Returns:
        dict 形如 ``{"total_return": ..., "annual_return": ..., ...}``，
        全部为 JSON 可序列化（``None`` 表示数据不足以计算）。
    """
    metrics: dict[str, float | int | None] = {
        "total_return": None,
        "annual_return": None,
        "max_drawdown": None,
        "sharpe_ratio": None,
        "win_rate": None,
        "trade_count": len(trades),
    }
    metrics.update(_compute_equity_metrics(equity_curve))
    metrics["win_rate"] = _safe_float(_compute_win_rate(trades))
    return metrics


# ---- equity_curve 派生指标 ----------------------------------------------

def _compute_equity_metrics(curve: Sequence[EquityPoint]) -> dict[str, float | None]:
    if len(curve) < 2:
        return {
            "total_return": None,
            "annual_return": None,
            "max_drawdown": None,
            "sharpe_ratio": None,
        }

    eq = np.array([p.equity for p in curve], dtype=float)
    n = len(eq)

    total_return = eq[-1] / eq[0] - 1.0

    # 年化：(1 + total)^(252/n) - 1
    if eq[0] > 0 and n > 0:
        annual_return = (1.0 + total_return) ** (TRADING_DAYS_PER_YEAR / n) - 1.0
    else:
        annual_return = None

    # 最大回撤：min_t (eq[t] / max(eq[0..t]) - 1)，取负值
    running_max = np.maximum.accumulate(eq)
    drawdowns = eq / running_max - 1.0
    max_drawdown = float(drawdowns.min())

    # 夏普：日收益率均值 / 标准差 * sqrt(252)
    daily_returns = np.diff(eq) / eq[:-1]
    if daily_returns.size > 1 and daily_returns.std(ddof=1) > 0:
        sharpe_ratio = float(
            daily_returns.mean() / daily_returns.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)
        )
    else:
        sharpe_ratio = None

    return {
        "total_return": _safe_float(total_return),
        "annual_return": _safe_float(annual_return),
        "max_drawdown": _safe_float(max_drawdown),
        "sharpe_ratio": _safe_float(sharpe_ratio),
    }


# ---- trades 派生指标 ----------------------------------------------------

def _compute_win_rate(trades: Sequence[Trade]) -> float | None:
    """按"BUY → 后续 SELL = 一笔完整交易"统计胜率。

    win 判据：``sell_proceeds_per_share > buy_cost_per_share``
    （已含买卖两侧的滑点 / 手续费）。
    """
    open_buy: Trade | None = None
    closed = 0
    wins = 0

    for t in trades:
        if t.action == "BUY":
            open_buy = t
        elif t.action == "SELL" and open_buy is not None and open_buy.quantity > 0:
            buy_cost_per_share = open_buy.price  # price 已含滑点
            # SELL 端 trade.price 是含滑点后的成交价
            sell_per_share = t.price
            if sell_per_share > buy_cost_per_share:
                wins += 1
            closed += 1
            open_buy = None

    if closed == 0:
        return None
    return wins / closed
