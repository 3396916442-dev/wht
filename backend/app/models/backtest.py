"""回测相关表：任务 / 结果 / 成交明细。"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

BigPK = BigInteger().with_variant(Integer, "sqlite")


# ---- 状态 / 动作常量 ---------------------------------------------------

class BacktestStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class TradeAction(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


# ---- 表 -----------------------------------------------------------------

class BacktestTask(Base):
    __tablename__ = "backtest_tasks"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(
        ForeignKey("strategies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    initial_cash: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False, default=Decimal("100000.00"))
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=BacktestStatus.PENDING.value, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # 关系（双向，便于 ORM 侧访问，不影响表结构）
    result: Mapped["BacktestResult | None"] = relationship(
        back_populates="task", uselist=False, cascade="all, delete-orphan"
    )
    trades: Mapped[list["BacktestTrade"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<BacktestTask id={self.id} strategy={self.strategy_id} {self.stock_code} {self.status}>"


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(BigPK, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("backtest_tasks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    total_return: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    annual_return: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    max_drawdown: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    sharpe_ratio: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    win_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    trade_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True, comment="完整指标 / 净值序列")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    task: Mapped[BacktestTask] = relationship(back_populates="result")


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"
    __table_args__ = (
        Index("ix_backtest_trades_task_date", "task_id", "trade_date"),
    )

    id: Mapped[int] = mapped_column(BigPK, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("backtest_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False, comment="BUY / SELL")
    price: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, comment="股数（A 股 100 股 = 1 手）")
    cash_after: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False, comment="成交后剩余现金")
    position_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="成交后持仓股数")
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="开/平仓原因（信号说明）")

    task: Mapped[BacktestTask] = relationship(back_populates="trades")
