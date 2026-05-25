"""策略层。

约定：
    - ``Strategy`` 抽象基类规定 ``generate_signals(bars) -> Series[Signal]`` 接口
    - 每个具体策略一个文件，复用现有指标
    - 策略只产生信号，不直接下单，便于复用到回测与实盘
"""

from app.strategy.base import Signal, Strategy
from app.strategy.ma_cross import MACrossStrategy

__all__ = ["Signal", "Strategy", "MACrossStrategy"]
