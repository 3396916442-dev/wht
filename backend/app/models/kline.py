"""日线行情表。"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, Index, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# 让 BigInteger 主键在 SQLite 下也能 AUTOINCREMENT（SQLite 本身只识别 INTEGER ROWID）
BigPK = BigInteger().with_variant(Integer, "sqlite")


class DailyBar(Base):
    __tablename__ = "daily_bars"
    __table_args__ = (
        UniqueConstraint("stock_code", "trade_date", name="uq_daily_bars_code_date"),
        Index("ix_daily_bars_code_date", "stock_code", "trade_date"),
        Index("ix_daily_bars_trade_date", "trade_date"),
    )

    id: Mapped[int] = mapped_column(BigPK, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, comment="股票代码")
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, comment="交易日")

    open: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)

    volume: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="成交量（手，1 手 = 100 股，与 akshare/tushare 原始单位一致）")
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False, comment="成交额（元）")
    pct_change: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True, comment="涨跌幅（%）")
    turnover: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True, comment="换手率（%）")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DailyBar {self.stock_code} {self.trade_date} close={self.close}>"
