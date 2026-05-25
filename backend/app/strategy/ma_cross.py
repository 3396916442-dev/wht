"""双均线策略：MA(short) 上穿 MA(long) 买入，下穿卖出。

防未来函数实现
==============
``signal[t]`` 仅依赖 ``close[0..t-1]``：

    fast = MA(close, short).shift(1)   # 截止 t-1 的快线
    slow = MA(close, long).shift(1)    # 截止 t-1 的慢线
    prev_fast = fast.shift(1)
    prev_slow = slow.shift(1)

    cross_up   = (prev_fast <= prev_slow) & (fast > slow)   # 金叉
    cross_down = (prev_fast >= prev_slow) & (fast < slow)   # 死叉

也就是说，**金叉 / 死叉的判断使用 t-2 与 t-1 两天的均值**，``signal[t]``
代表"在 t 日 open 执行"，t 日的 open / close 完全没有泄漏到信号生成中。
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.strategy.base import Signal, Strategy


class MACrossStrategy(Strategy):
    """``MA(short) / MA(long)`` 双均线交叉。"""

    def __init__(self, short_window: int = 5, long_window: int = 20) -> None:
        if short_window <= 0 or long_window <= 0:
            raise ValueError("short_window / long_window 必须为正整数")
        if short_window >= long_window:
            raise ValueError(f"short_window({short_window}) 必须小于 long_window({long_window})")
        self.short_window = short_window
        self.long_window = long_window

    @property
    def name(self) -> str:
        return f"ma_cross_{self.short_window}_{self.long_window}"

    @property
    def params(self) -> dict[str, Any]:
        return {"short_window": self.short_window, "long_window": self.long_window}

    def generate_signals(self, bars: pd.DataFrame) -> pd.Series:
        if "close" not in bars.columns:
            raise KeyError("MACrossStrategy: bars 缺少 close 列")

        close = bars["close"].astype(float)

        # 计算两条均线，并 shift(1)：让每行的 fast/slow 仅反映"昨日及更早"的信息
        fast = close.rolling(self.short_window, min_periods=self.short_window).mean().shift(1)
        slow = close.rolling(self.long_window, min_periods=self.long_window).mean().shift(1)

        prev_fast = fast.shift(1)
        prev_slow = slow.shift(1)

        cross_up = (prev_fast <= prev_slow) & (fast > slow)
        cross_down = (prev_fast >= prev_slow) & (fast < slow)

        signals = pd.Series(Signal.HOLD.value, index=bars.index, dtype="object")
        signals[cross_up.fillna(False)] = Signal.BUY.value
        signals[cross_down.fillna(False)] = Signal.SELL.value
        return signals
