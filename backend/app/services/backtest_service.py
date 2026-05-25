"""回测三张表的 CRUD + MA Cross 回测编排。"""

from __future__ import annotations

import logging
from datetime import date as date_t
from decimal import Decimal
from typing import Any, Iterable, Sequence

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.backtest import Broker, Portfolio, compute_metrics, run_backtest
from app.backtest.portfolio import LOT_SIZE, min_cash_for_one_lot
from app.models.backtest import (
    BacktestResult,
    BacktestStatus,
    BacktestTask,
    BacktestTrade,
)
from app.schemas.backtest import (
    BacktestResultCreate,
    BacktestTaskCreate,
    BacktestTaskUpdate,
    BacktestTradeCreate,
)
from app.schemas.strategy import StrategyCreate
from app.services.crud_base import CRUDBase
from app.services.stock_service import get_daily_bars
from app.services.strategy_service import strategy_service
from app.strategy.ma_cross import MACrossStrategy

logger = logging.getLogger("quant.service.backtest")


# ====================================================================
#  通用 CRUD（保留前一版本不变）
# ====================================================================

class BacktestTaskService(CRUDBase[BacktestTask, BacktestTaskCreate, BacktestTaskUpdate]):
    def list_by_status(
        self, db: Session, status: BacktestStatus | str, *, limit: int = 100
    ) -> Sequence[BacktestTask]:
        value = status.value if isinstance(status, BacktestStatus) else status
        stmt = (
            select(self.model)
            .where(self.model.status == value)
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        return db.execute(stmt).scalars().all()

    def mark_status(
        self, db: Session, task: BacktestTask, status: BacktestStatus | str
    ) -> BacktestTask:
        value = status.value if isinstance(status, BacktestStatus) else status
        return self.update(db, task, {"status": value})


class BacktestResultService(
    CRUDBase[BacktestResult, BacktestResultCreate, BacktestResultCreate]
):
    def get_by_task(self, db: Session, task_id: int) -> BacktestResult | None:
        stmt = select(self.model).where(self.model.task_id == task_id)
        return db.execute(stmt).scalar_one_or_none()


class BacktestTradeService(
    CRUDBase[BacktestTrade, BacktestTradeCreate, BacktestTradeCreate]
):
    def list_by_task(self, db: Session, task_id: int) -> Sequence[BacktestTrade]:
        stmt = (
            select(self.model)
            .where(self.model.task_id == task_id)
            .order_by(self.model.trade_date.asc(), self.model.id.asc())
        )
        return db.execute(stmt).scalars().all()

    def bulk_insert(
        self, db: Session, trades: Iterable[BacktestTradeCreate]
    ) -> int:
        rows = [BacktestTrade(**t.model_dump()) for t in trades]
        if not rows:
            return 0
        db.add_all(rows)
        db.commit()
        return len(rows)


backtest_task_service = BacktestTaskService(BacktestTask)
backtest_result_service = BacktestResultService(BacktestResult)
backtest_trade_service = BacktestTradeService(BacktestTrade)


# ====================================================================
#  MA Cross 回测：从「数据 → 引擎 → 持久化」端到端编排
# ====================================================================

def run_ma_cross_backtest(
    db: Session,
    *,
    stock_code: str,
    start_date: date_t,
    end_date: date_t,
    initial_cash: float = 100_000.0,
    short_window: int = 5,
    long_window: int = 20,
    commission_rate: float = 0.0003,
    stamp_tax_rate: float = 0.001,
    slippage_rate: float = 0.0005,
) -> dict[str, Any]:
    """运行双均线回测并把任务/结果/成交全部落库。

    返回的 dict 同时包含本次结果（指标 + trades + equity_curve）与 ``task_id``，
    上层 API 直接序列化即可。
    """
    if start_date > end_date:
        raise ValueError("start_date 不能晚于 end_date")
    strategy_obj = MACrossStrategy(short_window, long_window)  # 入参合法性在此校验

    # ---- 1. 找 / 建 strategy 元数据记录 ----------------------------
    strategy_record = _ensure_strategy_record(db, strategy_obj)

    # ---- 2. 建 task → RUNNING ---------------------------------------
    task = backtest_task_service.create(
        db,
        BacktestTaskCreate(
            strategy_id=strategy_record.id,
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
            initial_cash=Decimal(str(initial_cash)),
        ),
    )
    backtest_task_service.mark_status(db, task, BacktestStatus.RUNNING)

    try:
        # ---- 3. 取行情 ----------------------------------------------
        bars_df = _load_bars(db, stock_code, start_date, end_date, long_window)

        # ---- 4. 跑引擎 ----------------------------------------------
        signals = strategy_obj.generate_signals(bars_df)
        portfolio = Portfolio(initial_cash)
        broker = Broker(
            commission_rate=commission_rate,
            stamp_tax_rate=stamp_tax_rate,
            slippage_rate=slippage_rate,
        )
        _validate_initial_cash(
            initial_cash,
            stock_code=stock_code,
            bars_df=bars_df,
            broker=broker,
        )
        trades, equity_curve = run_backtest(bars_df, signals, portfolio, broker)
        metrics = compute_metrics(equity_curve, trades)

        # ---- 5. 持久化 result + trades ------------------------------
        equity_curve_json = [
            {
                "trade_date": p.trade_date.isoformat(),
                "cash": round(p.cash, 4),
                "position": p.position,
                "close": round(p.close, 4),
                "equity": round(p.equity, 4),
            }
            for p in equity_curve
        ]
        backtest_result_service.create(
            db,
            BacktestResultCreate(
                task_id=task.id,
                total_return=_to_decimal(metrics["total_return"]),
                annual_return=_to_decimal(metrics["annual_return"]),
                max_drawdown=_to_decimal(metrics["max_drawdown"]),
                sharpe_ratio=_to_decimal(metrics["sharpe_ratio"]),
                win_rate=_to_decimal(metrics["win_rate"]),
                trade_count=metrics["trade_count"],
                result_json={"equity_curve": equity_curve_json},
            ),
        )

        if trades:
            backtest_trade_service.bulk_insert(
                db,
                [
                    BacktestTradeCreate(
                        task_id=task.id,
                        stock_code=stock_code,
                        trade_date=t.trade_date,
                        action=t.action,
                        price=Decimal(str(round(t.price, 3))),
                        quantity=t.quantity,
                        cash_after=Decimal(str(round(t.cash_after, 2))),
                        position_after=t.position_after,
                        reason=t.reason,
                    )
                    for t in trades
                ],
            )

        backtest_task_service.mark_status(db, task, BacktestStatus.SUCCESS)
        logger.info(
            "ma_cross backtest done: task=%s stock=%s trades=%d total_return=%s",
            task.id, stock_code, len(trades), metrics["total_return"],
        )

        # ---- 6. 返回 -------------------------------------------------
        return {
            "task_id": task.id,
            "status": BacktestStatus.SUCCESS.value,
            "stock_code": stock_code,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "initial_cash": initial_cash,
            "params": strategy_obj.params,
            "metrics": metrics,
            "trades": [_trade_to_dict(t) for t in trades],
            "equity_curve": equity_curve_json,
        }

    except Exception as exc:
        logger.exception("ma_cross backtest failed: task=%s", task.id)
        backtest_task_service.mark_status(db, task, BacktestStatus.FAILED)
        raise


# ====================================================================
#  内部工具
# ====================================================================

def _ensure_strategy_record(db: Session, strategy_obj: MACrossStrategy):
    record = strategy_service.get_by_name(db, strategy_obj.name)
    if record is not None:
        return record
    return strategy_service.create(
        db,
        StrategyCreate(
            name=strategy_obj.name,
            type="ma_cross",
            description=f"{strategy_obj.short_window}/{strategy_obj.long_window} 双均线策略",
            params_json=strategy_obj.params,
        ),
    )


def _validate_initial_cash(
    initial_cash: float,
    *,
    stock_code: str,
    bars_df: pd.DataFrame,
    broker: Broker,
) -> None:
    """A 股最小 1 手 = 100 股；初始资金不足时策略信号无法成交。"""
    max_ref = float(bars_df[["open", "close"]].max().max())
    required = min_cash_for_one_lot(max_ref, broker)
    if initial_cash < required:
        raise ValueError(
            f"初始资金 {initial_cash:,.2f} 元不足以购买 1 手（{LOT_SIZE} 股）。"
            f"{stock_code} 在回测区间内最高成交价约 {max_ref:,.2f} 元/股，"
            f"至少需要约 {required:,.0f} 元（含滑点与买入手续费）。"
        )


def _load_bars(
    db: Session,
    stock_code: str,
    start_date: date_t,
    end_date: date_t,
    long_window: int,
) -> pd.DataFrame:
    bars = get_daily_bars(db, stock_code, start_date, end_date, limit=10000)
    # 至少需要 long_window + 2 行才能产生第一个信号（shift 两次后还有有效值）
    min_required = long_window + 2
    if len(bars) < min_required:
        raise ValueError(
            f"{stock_code} 在 [{start_date}, {end_date}] 的日线行数 {len(bars)} "
            f"少于 long_window+2={min_required}，请先同步更长区间或缩短 long_window"
        )

    df = pd.DataFrame(
        [
            {
                "trade_date": b.trade_date,
                "open": float(b.open),
                "high": float(b.high),
                "low": float(b.low),
                "close": float(b.close),
                "volume": int(b.volume),
            }
            for b in bars
        ]
    )
    return df.sort_values("trade_date").reset_index(drop=True)


def _to_decimal(value: float | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(round(value, 4)))


def _trade_to_dict(t) -> dict[str, Any]:
    return {
        "trade_date": t.trade_date.isoformat(),
        "action": t.action,
        "price": round(t.price, 3),
        "quantity": t.quantity,
        "cash_after": round(t.cash_after, 2),
        "position_after": t.position_after,
        "reason": t.reason,
    }


def get_backtest_detail(db: Session, task_id: int) -> dict[str, Any] | None:
    """从 DB 拼装一次完整回测结果，shape 与 :func:`run_ma_cross_backtest` 返回一致。

    返回 ``None`` 表示 task 不存在，由 API 层转 404。
    """
    task = backtest_task_service.get(db, task_id)
    if task is None:
        return None

    result = backtest_result_service.get_by_task(db, task_id)
    trades = backtest_trade_service.list_by_task(db, task_id)
    strategy_record = strategy_service.get(db, task.strategy_id)

    metrics: dict[str, Any] = {
        "total_return": _decimal_to_float(result.total_return) if result else None,
        "annual_return": _decimal_to_float(result.annual_return) if result else None,
        "max_drawdown": _decimal_to_float(result.max_drawdown) if result else None,
        "sharpe_ratio": _decimal_to_float(result.sharpe_ratio) if result else None,
        "win_rate": _decimal_to_float(result.win_rate) if result else None,
        "trade_count": result.trade_count if result else len(trades),
    }

    equity_curve = []
    if result and result.result_json:
        equity_curve = result.result_json.get("equity_curve", []) or []

    return {
        "task_id": task.id,
        "status": task.status,
        "stock_code": task.stock_code,
        "start_date": task.start_date.isoformat(),
        "end_date": task.end_date.isoformat(),
        "initial_cash": float(task.initial_cash),
        "params": (strategy_record.params_json if strategy_record else None) or {},
        "metrics": metrics,
        "trades": [
            {
                "trade_date": t.trade_date.isoformat(),
                "action": t.action,
                "price": float(t.price),
                "quantity": t.quantity,
                "cash_after": float(t.cash_after),
                "position_after": t.position_after,
                "reason": t.reason,
            }
            for t in trades
        ],
        "equity_curve": equity_curve,
    }


def list_backtest_tasks(
    db: Session,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """最近 N 条任务（含简略指标）。供前端列表 / 选择历史结果使用。"""
    tasks = backtest_task_service.list(db, skip=0, limit=limit)
    out: list[dict[str, Any]] = []
    for task in sorted(tasks, key=lambda t: t.created_at, reverse=True):
        result = backtest_result_service.get_by_task(db, task.id)
        out.append(
            {
                "task_id": task.id,
                "status": task.status,
                "stock_code": task.stock_code,
                "start_date": task.start_date.isoformat(),
                "end_date": task.end_date.isoformat(),
                "created_at": task.created_at.isoformat(),
                "total_return": _decimal_to_float(result.total_return) if result else None,
                "trade_count": result.trade_count if result else 0,
            }
        )
    return out


def _decimal_to_float(value) -> float | None:
    if value is None:
        return None
    return float(value)


__all__ = [
    "BacktestTaskService",
    "BacktestResultService",
    "BacktestTradeService",
    "backtest_task_service",
    "backtest_result_service",
    "backtest_trade_service",
    "run_ma_cross_backtest",
    "get_backtest_detail",
    "list_backtest_tasks",
]
