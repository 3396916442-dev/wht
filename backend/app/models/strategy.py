"""策略元信息表。"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True, comment="策略名（唯一）")
    type: Mapped[str] = mapped_column(String(50), nullable=False, comment="策略类型：ma_cross / momentum / ...")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    params_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True, comment="策略参数（JSON）")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Strategy {self.name} type={self.type}>"
