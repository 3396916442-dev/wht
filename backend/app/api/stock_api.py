"""股票相关接口。"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.stock_service import get_daily_with_indicators

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", summary="股票列表（占位）")
async def list_stocks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    keyword: str | None = Query(None, description="按代码或名称模糊搜索"),
) -> dict:
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
        "keyword": keyword,
        "detail": "to be implemented",
    }


@router.get("/{code}", summary="股票详情（占位）")
async def get_stock(code: str) -> dict:
    return {"code": code, "detail": "to be implemented"}


@router.get(
    "/{code}/daily",
    summary="获取股票日线行情（可选追加技术指标）",
    description=(
        "返回指定股票的日线序列，按 trade_date 升序。\n\n"
        "当 `indicators=true` 时，会在每条记录上追加：\n"
        "- `ma5` / `ma10` / `ma20` / `ma60`（移动平均线）\n"
        "- `rsi14`（相对强弱指标，Wilder 平滑）\n"
        "- `macd_dif` / `macd_dea` / `macd_hist`（默认 12/26/9，HIST 已 ×2 符合国内惯例）\n\n"
        "数据不足以计算时对应字段为 `null`。指标第一版实时计算，不入库。"
    ),
)
async def get_stock_daily(
    code: str,
    start_date: date | None = Query(None, description="起始日期 YYYY-MM-DD"),
    end_date: date | None = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(1000, ge=1, le=10000),
    indicators: bool = Query(
        False,
        description="为 true 时追加 MA(5/10/20/60) / RSI14 / MACD 指标列",
    ),
    db: Session = Depends(get_db),
) -> dict:
    items = get_daily_with_indicators(
        db,
        code,
        start_date,
        end_date,
        limit=limit,
        with_indicators=indicators,
    )
    return {
        "stock_code": code,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "indicators": indicators,
        "count": len(items),
        "items": items,
    }
