"""回测相关的数据契约：任务 / 结果 / 成交。"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ---- 任务 ---------------------------------------------------------------

class BacktestTaskBase(BaseModel):
    strategy_id: int
    stock_code: str = Field(..., max_length=20)
    start_date: date
    end_date: date
    initial_cash: Decimal = Field(default=Decimal("100000.00"), max_digits=20, decimal_places=2)


class BacktestTaskCreate(BacktestTaskBase):
    pass


class BacktestTaskUpdate(BaseModel):
    status: Literal["pending", "running", "success", "failed"] | None = None


class BacktestTaskRead(BacktestTaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime
    updated_at: datetime


# ---- 结果 ---------------------------------------------------------------

class BacktestResultBase(BaseModel):
    total_return: Decimal | None = Field(default=None, max_digits=10, decimal_places=4)
    annual_return: Decimal | None = Field(default=None, max_digits=10, decimal_places=4)
    max_drawdown: Decimal | None = Field(default=None, max_digits=10, decimal_places=4)
    sharpe_ratio: Decimal | None = Field(default=None, max_digits=10, decimal_places=4)
    win_rate: Decimal | None = Field(default=None, max_digits=10, decimal_places=4)
    trade_count: int = 0
    result_json: dict[str, Any] | None = None


class BacktestResultCreate(BacktestResultBase):
    task_id: int


class BacktestResultRead(BacktestResultBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    created_at: datetime


# ---- 成交 ---------------------------------------------------------------

class BacktestTradeBase(BaseModel):
    stock_code: str = Field(..., max_length=20)
    trade_date: date
    action: Literal["BUY", "SELL"]
    price: Decimal = Field(..., max_digits=10, decimal_places=3)
    quantity: int = Field(..., ge=0)
    cash_after: Decimal = Field(..., max_digits=20, decimal_places=2)
    position_after: int = Field(..., ge=0)
    reason: str | None = Field(default=None, max_length=255)


class BacktestTradeCreate(BacktestTradeBase):
    task_id: int


class BacktestTradeRead(BacktestTradeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
