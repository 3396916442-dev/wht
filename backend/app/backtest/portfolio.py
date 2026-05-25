"""资金 / 持仓状态机（单标的版本）。

约束：
    - **100 股整数倍**：A 股最小交易单元 1 手 = 100 股
    - **现金不足**：``buy_all`` 返回 ``None``
    - **持仓不足**：``sell_all`` 返回 ``None``
    - 第一版"全仓买入 / 全仓卖出"，不考虑分批 / 加减仓
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.backtest.broker import Broker

LOT_SIZE = 100


def min_cash_for_one_lot(
    ref_price: float,
    broker: Broker,
    *,
    lot_size: int = LOT_SIZE,
) -> float:
    """估算买入 1 手所需的最低现金（含滑点 + 买入手续费）。"""
    if ref_price <= 0:
        raise ValueError(f"ref_price 必须为正，收到：{ref_price}")
    exec_price = broker.adjust_buy_price(ref_price)
    cost_per_share = exec_price * (1.0 + broker.commission_rate)
    return cost_per_share * lot_size


@dataclass
class Trade:
    trade_date: date
    action: Literal["BUY", "SELL"]
    price: float           # 实际成交价（含滑点）
    quantity: int          # 股数（100 的整数倍）
    cash_after: float      # 成交后剩余现金
    position_after: int    # 成交后持仓股数
    reason: str | None = None


class Portfolio:
    """单标的全仓策略的资金/持仓容器。"""

    def __init__(self, initial_cash: float, *, lot_size: int = LOT_SIZE) -> None:
        if initial_cash <= 0:
            raise ValueError(f"initial_cash 必须为正，收到：{initial_cash}")
        if lot_size <= 0:
            raise ValueError(f"lot_size 必须为正，收到：{lot_size}")
        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.position = 0
        self.lot_size = lot_size

    # ---- 估值 -----------------------------------------------------------
    def equity(self, mark_price: float) -> float:
        """按 ``mark_price`` 计算当前总市值（现金 + 持仓估值）。"""
        return self.cash + self.position * mark_price

    # ---- 交易 -----------------------------------------------------------
    def buy_all(
        self,
        ref_price: float,
        broker: Broker,
        trade_date: date,
        reason: str | None = None,
    ) -> Trade | None:
        """全仓买入。返回成交记录；现金不足以买 1 手则返回 ``None``。

        计算流程：
            1. ``exec_price = ref_price * (1 + slippage)``
            2. 用全部现金能买的最大手数 ``k`` 满足
               ``exec_price * k * lot * (1 + commission_rate) <= cash``
            3. 实际成交：扣 ``gross + commission``，持仓 += k * lot
        """
        exec_price = broker.adjust_buy_price(ref_price)
        cost_per_share_with_fee = exec_price * (1.0 + broker.commission_rate)

        max_shares = int(self.cash // cost_per_share_with_fee)
        qty = (max_shares // self.lot_size) * self.lot_size
        if qty <= 0:
            return None

        gross = exec_price * qty
        commission = broker.buy_fee(gross)
        total_cost = gross + commission

        # 浮点保护：total_cost 极小幅度可能浮过 cash，回退一手再试
        while total_cost > self.cash and qty > 0:
            qty -= self.lot_size
            gross = exec_price * qty
            commission = broker.buy_fee(gross)
            total_cost = gross + commission
        if qty <= 0:
            return None

        self.cash -= total_cost
        self.position += qty

        return Trade(
            trade_date=trade_date,
            action="BUY",
            price=exec_price,
            quantity=qty,
            cash_after=self.cash,
            position_after=self.position,
            reason=reason,
        )

    def sell_all(
        self,
        ref_price: float,
        broker: Broker,
        trade_date: date,
        reason: str | None = None,
    ) -> Trade | None:
        """全仓卖出。无持仓时返回 ``None``。"""
        if self.position <= 0:
            return None

        qty = self.position
        exec_price = broker.adjust_sell_price(ref_price)
        gross = exec_price * qty
        fee = broker.sell_fee(gross)
        net_proceeds = gross - fee

        self.cash += net_proceeds
        self.position = 0

        return Trade(
            trade_date=trade_date,
            action="SELL",
            price=exec_price,
            quantity=qty,
            cash_after=self.cash,
            position_after=self.position,
            reason=reason,
        )
