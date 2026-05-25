"""StockBasic 的数据契约。"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class StockBasicBase(BaseModel):
    code: str = Field(..., max_length=20, examples=["600519"])
    name: str = Field(..., max_length=50, examples=["贵州茅台"])
    market: str = Field(..., max_length=10, examples=["SH"])
    industry: str | None = Field(default=None, max_length=50)
    list_date: date | None = None


class StockBasicCreate(StockBasicBase):
    pass


class StockBasicUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    market: str | None = Field(default=None, max_length=10)
    industry: str | None = Field(default=None, max_length=50)
    list_date: date | None = None


class StockBasicRead(StockBasicBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
