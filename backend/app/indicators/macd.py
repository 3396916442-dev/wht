"""异同移动平均线（MACD, Moving Average Convergence Divergence）。

公式（默认参数 12 / 26 / 9）::

    EMA_fast = EMA(close, span=fast)
    EMA_slow = EMA(close, span=slow)
    DIF      = EMA_fast - EMA_slow
    DEA      = EMA(DIF, span=signal)        # 也叫 SIGNAL
    HIST     = 2 * (DIF - DEA)              # ↓ 国内惯例柱线放大 2 倍

国内 / 国外区别：
    - 国内 K 线软件（同花顺 / 通达信 / 东方财富）展示的 MACD 柱 = 2*(DIF - DEA)
    - 国外（TA-Lib / Investopedia）通常 HIST = DIF - DEA（不乘 2）
    本平台采用国内惯例。
"""

from __future__ import annotations

import pandas as pd


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """计算 MACD 三件套，返回 ``(DIF, DEA, HIST)``。"""
    if not (fast > 0 and slow > 0 and signal > 0):
        raise ValueError("fast / slow / signal 必须均为正整数")
    if fast >= slow:
        raise ValueError(f"fast({fast}) 必须小于 slow({slow})")

    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    hist = (dif - dea) * 2
    return dif, dea, hist


def add_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    *,
    source_col: str = "close",
) -> pd.DataFrame:
    """追加 ``macd_dif`` / ``macd_dea`` / ``macd_hist`` 三列。"""
    if source_col not in df.columns:
        raise KeyError(f"add_macd: DataFrame 缺少列 {source_col!r}")
    out = df.copy()
    dif, dea, hist = macd(out[source_col], fast, slow, signal)
    out["macd_dif"] = dif
    out["macd_dea"] = dea
    out["macd_hist"] = hist
    return out
