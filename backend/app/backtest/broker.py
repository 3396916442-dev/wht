"""撮合 / 费率模型。

第一版只实现 A 股最常用的三个成本：
    - **滑点**：买入按 ``price * (1 + slippage)`` 成交，卖出按 ``price * (1 - slippage)``
    - **手续费**：双向，``成交金额 * commission_rate``
    - **印花税**：仅卖出，``成交金额 * stamp_tax_rate``

约定：所有费率以**小数**表示（万三 = 0.0003）。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Broker:
    commission_rate: float = 0.0003
    stamp_tax_rate: float = 0.001
    slippage_rate: float = 0.0005

    def __post_init__(self) -> None:
        for name, value in (
            ("commission_rate", self.commission_rate),
            ("stamp_tax_rate", self.stamp_tax_rate),
            ("slippage_rate", self.slippage_rate),
        ):
            if value < 0:
                raise ValueError(f"{name} 不能为负，收到：{value}")

    # ---- 价格调整 -------------------------------------------------------
    def adjust_buy_price(self, price: float) -> float:
        return price * (1.0 + self.slippage_rate)

    def adjust_sell_price(self, price: float) -> float:
        return price * (1.0 - self.slippage_rate)

    # ---- 费用 -----------------------------------------------------------
    def buy_fee(self, gross_amount: float) -> float:
        """买入手续费。"""
        return gross_amount * self.commission_rate

    def sell_fee(self, gross_amount: float) -> float:
        """卖出手续费 + 印花税。"""
        return gross_amount * (self.commission_rate + self.stamp_tax_rate)
