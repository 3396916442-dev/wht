"""Strategy CRUD。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.schemas.strategy import StrategyCreate, StrategyUpdate
from app.services.crud_base import CRUDBase


class StrategyService(CRUDBase[Strategy, StrategyCreate, StrategyUpdate]):
    def get_by_name(self, db: Session, name: str) -> Strategy | None:
        stmt = select(self.model).where(self.model.name == name)
        return db.execute(stmt).scalar_one_or_none()


strategy_service = StrategyService(Strategy)
