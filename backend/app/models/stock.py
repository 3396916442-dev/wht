"""股票基础信息表。"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StockBasic(Base):
    __tablename__ = "stock_basic"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True, comment="股票代码，例如 600519")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="股票名称")
    market: Mapped[str] = mapped_column(String(10), nullable=False, comment="市场：SH / SZ / BJ")
    industry: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="所属行业")
    list_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="上市日期")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return f"<StockBasic {self.code} {self.name}>"
