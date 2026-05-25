"""Strategy 的数据契约。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrategyBase(BaseModel):
    name: str = Field(..., max_length=100)
    type: str = Field(..., max_length=50)
    description: str | None = None
    params_json: dict[str, Any] | None = None


class StrategyCreate(StrategyBase):
    pass


class StrategyUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    type: str | None = Field(default=None, max_length=50)
    description: str | None = None
    params_json: dict[str, Any] | None = None


class StrategyRead(StrategyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
