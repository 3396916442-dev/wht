"""技术指标模块。

每个指标提供两层：
    - 低层纯函数：``ma`` / ``rsi`` / ``macd`` / ``boll`` —— 输入 ``Series``，便于在策略 / 回测中精细控制
    - 高层包装：``add_ma`` / ``add_rsi`` / ``add_macd`` / ``add_boll`` —— 在 DataFrame 上追加列

统一入口 :func:`apply_indicators` 按名称列表批量追加，API 层用它即可。

第一版必须实现：MA5 / MA10 / MA20 / MA60 / RSI14 / MACD（12/26/9）。
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from app.indicators.boll import add_boll, boll
from app.indicators.ma import DEFAULT_WINDOWS as MA_DEFAULT_WINDOWS
from app.indicators.ma import add_ma, ma
from app.indicators.macd import add_macd, macd
from app.indicators.rsi import add_rsi, rsi

__all__ = [
    "ma", "add_ma", "MA_DEFAULT_WINDOWS",
    "rsi", "add_rsi",
    "macd", "add_macd",
    "boll", "add_boll",
    "apply_indicators",
    "DEFAULT_INDICATORS",
    "INDICATOR_OUTPUT_COLUMNS",
]

# 第一版默认追加的指标集合
DEFAULT_INDICATORS: tuple[str, ...] = ("ma", "rsi", "macd")

# 各指标对应输出列（用于文档 / 测试断言）
INDICATOR_OUTPUT_COLUMNS: dict[str, tuple[str, ...]] = {
    "ma": ("ma5", "ma10", "ma20", "ma60"),
    "rsi": ("rsi14",),
    "macd": ("macd_dif", "macd_dea", "macd_hist"),
    "boll": ("boll_upper", "boll_mid", "boll_lower"),
}


def apply_indicators(
    df: pd.DataFrame,
    indicators: Iterable[str] | None = None,
) -> pd.DataFrame:
    """按名称批量追加指标列。

    Args:
        df: 至少包含 ``close`` 列的日线 DataFrame，应**已按 trade_date 升序**。
        indicators: 指标名称列表，支持 ``"ma" / "rsi" / "macd" / "boll"``，
            ``None`` 时使用 :data:`DEFAULT_INDICATORS`。

    Returns:
        新的 DataFrame（不修改输入）。
    """
    names = tuple(indicators) if indicators is not None else DEFAULT_INDICATORS
    out = df
    for name in names:
        n = name.lower()
        if n == "ma":
            out = add_ma(out)
        elif n == "rsi":
            out = add_rsi(out)
        elif n == "macd":
            out = add_macd(out)
        elif n == "boll":
            out = add_boll(out)
        else:
            raise ValueError(
                f"未知指标：{name!r}（支持：{list(INDICATOR_OUTPUT_COLUMNS)}）"
            )
    return out
