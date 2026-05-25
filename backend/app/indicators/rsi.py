"""相对强弱指标（RSI, Relative Strength Index）。

采用 J. Welles Wilder 的指数平滑（``alpha = 1/period``、``adjust=False``），
等价于业界 / TA-Lib 默认 RSI 的标准定义::

    delta     = close.diff()
    gain      = max(delta, 0)
    loss      = -min(delta, 0)
    avg_gain  = EMA_Wilder(gain, period)
    avg_loss  = EMA_Wilder(loss, period)
    RS        = avg_gain / avg_loss
    RSI       = 100 - 100 / (1 + RS)

边界处理：
    - 前 ``period`` 行数据不足，返回 ``NaN``。
    - 纯上涨区间（``avg_loss == 0`` 且 ``avg_gain > 0``）→ ``RSI = 100``。
    - 完全平盘（``avg_gain == avg_loss == 0``）→ ``RSI = NaN``（金融语义未定义）。
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    if period <= 0:
        raise ValueError(f"period 必须为正整数，收到：{period}")

    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

    # 用 NaN 替换 0，避免除零警告；flat 段会自然得到 NaN
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)

    # 纯上涨：avg_loss==0 且 avg_gain>0 → RSI=100
    pure_up = (avg_loss == 0) & (avg_gain > 0)
    out = out.where(~pure_up, 100.0)

    # 前 period 行不稳定，统一返回 NaN
    if len(out) >= period:
        out.iloc[:period] = np.nan
    else:
        out.iloc[:] = np.nan

    return out


def add_rsi(
    df: pd.DataFrame,
    period: int = 14,
    *,
    source_col: str = "close",
    out_col: str | None = None,
) -> pd.DataFrame:
    """追加 ``rsi{period}`` 列（默认 ``rsi14``）。"""
    if source_col not in df.columns:
        raise KeyError(f"add_rsi: DataFrame 缺少列 {source_col!r}")
    out = df.copy()
    out[out_col or f"rsi{period}"] = rsi(out[source_col], period)
    return out
