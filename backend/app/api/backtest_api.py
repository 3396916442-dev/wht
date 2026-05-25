"""回测相关接口。"""

from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.ai import generate_report
from app.core.database import get_db
from app.services.backtest_service import (
    get_backtest_detail,
    list_backtest_tasks,
    run_ma_cross_backtest,
)

logger = logging.getLogger("quant.api.backtest")

router = APIRouter(prefix="/backtest", tags=["backtest"])


# ---- 占位（保留，后期通用任务调度器接入）-------------------------------

@router.post("/run", summary="提交回测任务（占位，沿用至通用调度器接入）")
async def run_backtest_placeholder() -> dict:
    return {
        "task_id": "stub-task-id",
        "status": "queued",
        "detail": "to be implemented; 第一版请改用 POST /backtest/ma-cross",
    }


# ---- 任务列表 -----------------------------------------------------------

@router.get("/tasks", summary="最近回测任务列表")
async def list_tasks(
    limit: int = 50,
    db: Session = Depends(get_db),
) -> dict:
    items = list_backtest_tasks(db, limit=limit)
    return {"count": len(items), "items": items}


# ---- 单次回测详情 -------------------------------------------------------

@router.get(
    "/{task_id}",
    summary="查询某次回测的完整结果（指标 + 交易 + 净值曲线）",
)
async def get_backtest_result(
    task_id: int,
    db: Session = Depends(get_db),
) -> dict:
    detail = get_backtest_detail(db, task_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"backtest task {task_id} not found",
        )
    return detail


@router.get(
    "/{task_id}/report",
    summary="生成回测中文分析报告（第一版规则化，不调用大模型）",
    description=(
        "基于回测结果按阈值规则生成结构化中文报告，包含总体表现 / 收益 / 回撤 / "
        "交易频率 / 胜率 / 过拟合提醒 / 风险声明。响应中 `provider` 标明来源，"
        "第一版固定为 `rule-based`。"
    ),
)
async def get_backtest_report(
    task_id: int,
    db: Session = Depends(get_db),
) -> dict:
    detail = get_backtest_detail(db, task_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"backtest task {task_id} not found",
        )
    return generate_report(detail)


# ---- MA Cross 回测 -------------------------------------------------------

class MACrossBacktestRequest(BaseModel):
    stock_code: str = Field(..., max_length=20, examples=["600519"])
    start_date: date
    end_date: date
    initial_cash: float = Field(500_000.0, gt=0, le=1e10)
    short_window: int = Field(5, ge=1, le=120)
    long_window: int = Field(20, ge=2, le=250)
    commission_rate: float = Field(0.0003, ge=0, le=0.01)
    stamp_tax_rate: float = Field(0.001, ge=0, le=0.01)
    slippage_rate: float = Field(0.0005, ge=0, le=0.01)

    @model_validator(mode="after")
    def _check_windows(self) -> "MACrossBacktestRequest":
        if self.short_window >= self.long_window:
            raise ValueError(
                f"short_window({self.short_window}) 必须小于 long_window({self.long_window})"
            )
        if self.start_date > self.end_date:
            raise ValueError("start_date 不能晚于 end_date")
        return self


@router.post(
    "/ma-cross",
    summary="运行双均线回测（MA short 上穿 long 买入，下穿卖出）",
    description=(
        "单股票全仓回测，避免未来函数（信号仅基于 t-1 及之前数据，"
        "在 t 日 open 成交，t 日 close 估值）。\n\n"
        "回测结果会写入 `backtest_tasks` / `backtest_results` / `backtest_trades` 三张表。"
    ),
)
async def run_ma_cross(
    payload: MACrossBacktestRequest = Body(...),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return run_ma_cross_backtest(
            db,
            stock_code=payload.stock_code,
            start_date=payload.start_date,
            end_date=payload.end_date,
            initial_cash=payload.initial_cash,
            short_window=payload.short_window,
            long_window=payload.long_window,
            commission_rate=payload.commission_rate,
            stamp_tax_rate=payload.stamp_tax_rate,
            slippage_rate=payload.slippage_rate,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("ma_cross backtest internal error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"回测执行失败：{exc}",
        ) from exc
