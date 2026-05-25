"""策略抽象基类。

策略只负责"输入 K 线 → 输出信号序列"，不接触资金 / 持仓 / 撮合。
便于在回测、实盘下单、可视化标注三处复用。

信号语义
========
:func:`Strategy.generate_signals` 返回的 ``signal[t]`` 表示
**在第 t 日的 open 价上执行的动作**。

为了避免"未来函数"，实现层在生成 ``signal[t]`` 时只能使用 ``t - 1`` 及更早
的 K 线数据；最常见的做法是先用全量数据计算指标，再对指标 ``shift(1)`` 让
判断点延后一日（见 :class:`MACrossStrategy`）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any

import pandas as pd


class Signal(StrEnum):
    """开/平仓信号。"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Strategy(ABC):
    """所有策略的抽象基类。"""

    name: str = "base"

    @abstractmethod
    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        """生成与 ``bars`` 同 index 的信号序列。

        Args:
            bars: 必须包含 ``trade_date`` / ``open`` / ``high`` / ``low`` /
                ``close`` / ``volume`` 列，按 ``trade_date`` 升序。

        Returns:
            ``pd.Series[Signal]`` 长度等于 ``len(bars)``。
            前 N 行通常是 ``Signal.HOLD``（指标尚未生效）。
        """

    @property
    def params(self) -> dict[str, Any]:
        """策略参数（用于持久化到 ``strategies.params_json``）。"""
        return {}
