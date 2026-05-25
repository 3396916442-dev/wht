"""DailyBar CRUD。

考虑日线写入是高频 / 批量场景，提供 ``bulk_insert`` 接口；
更新逻辑（覆盖旧数据）放到后续数据同步任务里实现。
"""

from __future__ import annotations

from datetime import date as date_t
from typing import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.kline import DailyBar
from app.schemas.kline import DailyBarCreate
from app.services.crud_base import CRUDBase


class DailyBarService(CRUDBase[DailyBar, DailyBarCreate, DailyBarCreate]):
    def get_by_code_date(
        self, db: Session, stock_code: str, trade_date: date_t
    ) -> DailyBar | None:
        stmt = select(self.model).where(
            self.model.stock_code == stock_code,
            self.model.trade_date == trade_date,
        )
        return db.execute(stmt).scalar_one_or_none()

    def list_by_code(
        self,
        db: Session,
        stock_code: str,
        *,
        start: date_t | None = None,
        end: date_t | None = None,
        limit: int = 1000,
    ) -> Sequence[DailyBar]:
        stmt = select(self.model).where(self.model.stock_code == stock_code)
        if start is not None:
            stmt = stmt.where(self.model.trade_date >= start)
        if end is not None:
            stmt = stmt.where(self.model.trade_date <= end)
        stmt = stmt.order_by(self.model.trade_date.asc()).limit(limit)
        return db.execute(stmt).scalars().all()

    def bulk_insert(self, db: Session, bars: Iterable[DailyBarCreate]) -> int:
        """批量插入。冲突处理由调用方保证（先删旧、或捕获唯一索引冲突）。"""
        rows = [DailyBar(**bar.model_dump()) for bar in bars]
        if not rows:
            return 0
        db.add_all(rows)
        db.commit()
        return len(rows)


daily_bar_service = DailyBarService(DailyBar)
