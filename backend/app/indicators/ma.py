"""移动平均线（MA / SMA）。

约定：
    - 输入 ``pandas.Series``（通常是 close）
    - 前 ``window-1`` 行返回 ``NaN``（``min_periods=window``，符合金融惯例：MA5 至少要有 5 天才算）
"""

from __future__ import annotations

from typing import Sequence

import pandas as pd

DEFAULT_WINDOWS: tuple[int, ...] = (5, 10, 20, 60)


def ma(series: pd.Series, window: int) -> pd.Series:
    """简单移动平均（SMA）。"""
    if window <= 0:
        raise ValueError(f"window 必须为正整数，收到：{window}")
    return series.rolling(window=window, min_periods=window).mean()


def add_ma(
    df: pd.DataFrame,
    windows: Sequence[int] = DEFAULT_WINDOWS,
    *,
    source_col: str = "close",
) -> pd.DataFrame:
    """对 ``df[source_col]`` 计算多个 MA 列，追加为 ``ma{N}``（如 ``ma5`` / ``ma10`` / ``ma20`` / ``ma60``）。

    返回新 DataFrame，**不修改原 df**。
    """
    if source_col not in df.columns:
        raise KeyError(f"add_ma: DataFrame 缺少列 {source_col!r}")
    out = df.copy()
    for w in windows:
        out[f"ma{w}"] = ma(out[source_col], w)
    return out
