"""布林带（Bollinger Bands）。

公式（默认 ``period=20``、``std_mult=2.0``）::

    mid   = SMA(close, period)
    std   = STD(close, period, ddof=0)        # 总体标准差，与同花顺一致
    upper = mid + std_mult * std
    lower = mid - std_mult * std

第一版接口预留，前端展示阶段会真正用到。
"""

from __future__ import annotations

import pandas as pd


def boll(
    series: pd.Series,
    period: int = 20,
    std_mult: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """返回 ``(upper, mid, lower)`` 三条线。"""
    if period <= 0:
        raise ValueError(f"period 必须为正整数，收到：{period}")
    if std_mult <= 0:
        raise ValueError(f"std_mult 必须为正数，收到：{std_mult}")

    mid = series.rolling(window=period, min_periods=period).mean()
    std = series.rolling(window=period, min_periods=period).std(ddof=0)
    upper = mid + std_mult * std
    lower = mid - std_mult * std
    return upper, mid, lower


def add_boll(
    df: pd.DataFrame,
    period: int = 20,
    std_mult: float = 2.0,
    *,
    source_col: str = "close",
) -> pd.DataFrame:
    """追加 ``boll_upper`` / ``boll_mid`` / ``boll_lower`` 三列。"""
    if source_col not in df.columns:
        raise KeyError(f"add_boll: DataFrame 缺少列 {source_col!r}")
    out = df.copy()
    upper, mid, lower = boll(out[source_col], period, std_mult)
    out["boll_upper"] = upper
    out["boll_mid"] = mid
    out["boll_lower"] = lower
    return out
