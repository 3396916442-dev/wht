"""通用 CRUD 基类。

子类只需指定 ``ModelType`` / ``CreateSchemaType`` / ``UpdateSchemaType``
即可获得 get / list / create / update / delete / count 等基础能力。
领域特化方法在子类里追加（例如 ``get_by_code``）。
"""

from __future__ import annotations

from typing import Any, Generic, Sequence, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    # ---- 读 -----------------------------------------------------------

    def get(self, db: Session, id: int) -> ModelType | None:
        return db.get(self.model, id)

    def list(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        return db.execute(stmt).scalars().all()

    def count(self, db: Session) -> int:
        stmt = select(func.count()).select_from(self.model)
        return int(db.execute(stmt).scalar_one())

    # ---- 写 -----------------------------------------------------------

    def create(self, db: Session, obj_in: CreateSchemaType | dict[str, Any]) -> ModelType:
        data = obj_in.model_dump() if isinstance(obj_in, BaseModel) else dict(obj_in)
        obj = self.model(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(
        self,
        db: Session,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        data = (
            obj_in.model_dump(exclude_unset=True)
            if isinstance(obj_in, BaseModel)
            else dict(obj_in)
        )
        for field, value in data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> ModelType | None:
        obj = db.get(self.model, id)
        if obj is None:
            return None
        db.delete(obj)
        db.commit()
        return obj
