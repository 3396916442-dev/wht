"""DailyBar 的数据契约。"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DailyBarBase(BaseModel):
    stock_code: str = Field(..., max_length=20)
    trade_date: date

    open: Decimal = Field(..., max_digits=10, decimal_places=3)
    high: Decimal = Field(..., max_digits=10, decimal_places=3)
    low: Decimal = Field(..., max_digits=10, decimal_places=3)
    close: Decimal = Field(..., max_digits=10, decimal_places=3)

    volume: int = Field(..., ge=0)
    amount: Decimal = Field(..., max_digits=20, decimal_places=2)
    pct_change: Decimal | None = Field(default=None, max_digits=10, decimal_places=4)
    turnover: Decimal | None = Field(default=None, max_digits=10, decimal_places=4)


class DailyBarCreate(DailyBarBase):
    pass


class DailyBarRead(DailyBarBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
