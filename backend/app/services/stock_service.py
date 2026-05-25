"""股票相关业务服务。

包含两类对外能力：

1. ``StockService`` 类 + ``stock_service`` 单例：``stock_basic`` 表的 CRUD。
2. 模块级日线函数（行情同步链路常用）：

    - :func:`fetch_stock_daily_from_akshare` —— 透传 akshare 客户端
    - :func:`save_daily_bars`                —— upsert 到 ``daily_bars``
    - :func:`get_daily_bars`                 —— 按代码 / 日期范围查询
    - :func:`sync_daily_bars`                —— fetch + save 一站式

upsert 在 MySQL 走 ``INSERT ... ON DUPLICATE KEY UPDATE``，
在 SQLite 走 ``INSERT ... ON CONFLICT DO UPDATE``，都依赖
``daily_bars`` 上 ``(stock_code, trade_date)`` 的唯一索引。
"""

from __future__ import annotations

import logging
from datetime import date as date_t
from typing import Any, Iterable, Sequence

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.akshare_client import (  # re-export 方便调用方
    AkshareError,
    fetch_stock_daily_from_akshare,
)
from app.indicators import apply_indicators
from app.models.kline import DailyBar
from app.models.stock import StockBasic
from app.schemas.stock import StockBasicCreate, StockBasicUpdate
from app.services.crud_base import CRUDBase

logger = logging.getLogger("quant.service.stock")

__all__ = [
    "StockService",
    "stock_service",
    "fetch_stock_daily_from_akshare",
    "save_daily_bars",
    "get_daily_bars",
    "sync_daily_bars",
    "get_daily_with_indicators",
    "AkshareError",
]


# ---- StockBasic CRUD ----------------------------------------------------

class StockService(CRUDBase[StockBasic, StockBasicCreate, StockBasicUpdate]):
    def get_by_code(self, db: Session, code: str) -> StockBasic | None:
        stmt = select(self.model).where(self.model.code == code)
        return db.execute(stmt).scalar_one_or_none()

    def upsert_by_code(self, db: Session, payload: StockBasicCreate) -> StockBasic:
        existing = self.get_by_code(db, payload.code)
        if existing is None:
            return self.create(db, payload)
        return self.update(db, existing, payload.model_dump())


stock_service = StockService(StockBasic)


# ---- 日线模块级业务函数 -------------------------------------------------

# 唯一索引外的所有可变字段（upsert 时需要覆盖）
_DAILY_UPDATE_COLS: tuple[str, ...] = (
    "open", "high", "low", "close", "volume", "amount", "pct_change", "turnover",
)


def _normalize_date(value: Any) -> date_t:
    if isinstance(value, date_t):
        return value
    if isinstance(value, str):
        # 接受 "YYYY-MM-DD" / "YYYY/MM/DD"
        s = value.replace("/", "-")
        return date_t.fromisoformat(s)
    raise TypeError(f"unsupported trade_date type: {type(value).__name__}")


def _normalize_rows(stock_code: str, rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in rows:
        nr = dict(r)
        nr.setdefault("stock_code", stock_code)
        nr["trade_date"] = _normalize_date(nr["trade_date"])
        out.append(nr)
    return out


def save_daily_bars(
    db: Session,
    stock_code: str,
    rows: Iterable[dict[str, Any]],
) -> dict[str, int]:
    """将日线数据批量 upsert 到 ``daily_bars``。

    冲突键为 ``(stock_code, trade_date)``，已存在则覆盖更新所有 OHLCV 字段。

    Returns:
        ``{"total": 总行数, "affected": 受影响行数}``。
        - MySQL 的 ``affected`` 中：插入计 1，更新计 2，无变化计 0（MySQL 原生语义）。
        - SQLite / 兜底分支：``affected`` 取本批写入数量。
    """
    normalized = _normalize_rows(stock_code, rows)
    if not normalized:
        logger.info("save_daily_bars: empty input for %s", stock_code)
        return {"total": 0, "affected": 0}

    dialect = db.bind.dialect.name if db.bind is not None else ""
    logger.info(
        "save_daily_bars: stock=%s rows=%d dialect=%s",
        stock_code, len(normalized), dialect,
    )

    if dialect == "mysql":
        from sqlalchemy.dialects.mysql import insert as mysql_insert

        stmt = mysql_insert(DailyBar).values(normalized)
        stmt = stmt.on_duplicate_key_update(
            **{col: stmt.inserted[col] for col in _DAILY_UPDATE_COLS}
        )
        result = db.execute(stmt)
        db.commit()
        return {"total": len(normalized), "affected": int(result.rowcount or 0)}

    if dialect == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        stmt = sqlite_insert(DailyBar).values(normalized)
        stmt = stmt.on_conflict_do_update(
            index_elements=["stock_code", "trade_date"],
            set_={col: stmt.excluded[col] for col in _DAILY_UPDATE_COLS},
        )
        db.execute(stmt)
        db.commit()
        return {"total": len(normalized), "affected": len(normalized)}

    # 兜底：逐条先查后写（其它方言 / 未来切换数据库时仍能跑通）
    logger.warning("save_daily_bars fallback path for dialect=%s", dialect)
    affected = 0
    for r in normalized:
        existing = db.execute(
            select(DailyBar).where(
                DailyBar.stock_code == r["stock_code"],
                DailyBar.trade_date == r["trade_date"],
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(DailyBar(**r))
        else:
            for col in _DAILY_UPDATE_COLS:
                if col in r:
                    setattr(existing, col, r[col])
        affected += 1
    db.commit()
    return {"total": len(normalized), "affected": affected}


def get_daily_bars(
    db: Session,
    stock_code: str,
    start_date: date_t | str | None = None,
    end_date: date_t | str | None = None,
    *,
    limit: int = 1000,
) -> Sequence[DailyBar]:
    """按代码 + 日期范围读取日线（升序，受 limit 限制）。"""
    start = _normalize_date(start_date) if start_date else None
    end = _normalize_date(end_date) if end_date else None

    stmt = select(DailyBar).where(DailyBar.stock_code == stock_code)
    if start is not None:
        stmt = stmt.where(DailyBar.trade_date >= start)
    if end is not None:
        stmt = stmt.where(DailyBar.trade_date <= end)
    stmt = stmt.order_by(DailyBar.trade_date.asc()).limit(limit)
    return db.execute(stmt).scalars().all()


def sync_daily_bars(
    db: Session,
    stock_code: str,
    start_date: date_t | str,
    end_date: date_t | str,
    *,
    adjust: str = "",
) -> dict[str, Any]:
    """从 akshare 拉取 ``stock_code`` 的日线并写入数据库。

    异常透传给上层（API 层会转成 502）。
    """
    rows = fetch_stock_daily_from_akshare(
        stock_code, start_date, end_date, adjust=adjust
    )
    saved = save_daily_bars(db, stock_code, rows)
    logger.info(
        "sync_daily_bars done: stock=%s fetched=%d saved=%s",
        stock_code, len(rows), saved,
    )
    return {
        "stock_code": stock_code,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "fetched": len(rows),
        "saved": saved,
    }


# ---- 序列化：DailyBar → JSON-friendly dict（含可选指标）------------------

_PRICE_COLS: frozenset[str] = frozenset({"open", "high", "low", "close", "amount"})
_PRICE_DIGITS = 3
_INDICATOR_DIGITS = 4


def _bars_to_df(bars: Sequence[DailyBar]) -> pd.DataFrame:
    """将 ORM 行转换为按 trade_date 升序的 DataFrame（指标计算前置步骤）。"""
    return pd.DataFrame(
        [
            {
                "trade_date": b.trade_date,
                "open": float(b.open),
                "high": float(b.high),
                "low": float(b.low),
                "close": float(b.close),
                "volume": int(b.volume),
                "amount": float(b.amount),
                "pct_change": float(b.pct_change) if b.pct_change is not None else None,
            }
            for b in bars
        ]
    ).sort_values("trade_date").reset_index(drop=True)


def _row_to_item(row: pd.Series) -> dict[str, Any]:
    """单行 → 可序列化 dict：NaN→None / 价格 3 位 / 指标 4 位 / 日期 ISO。"""
    item: dict[str, Any] = {}
    for col, val in row.items():
        if pd.isna(val):
            item[col] = None
        elif col == "trade_date":
            item[col] = val.isoformat() if hasattr(val, "isoformat") else str(val)
        elif col == "volume":
            item[col] = int(val)
        else:
            digits = _PRICE_DIGITS if col in _PRICE_COLS else _INDICATOR_DIGITS
            item[col] = round(float(val), digits)
    return item


def get_daily_with_indicators(
    db: Session,
    stock_code: str,
    start_date: date_t | str | None = None,
    end_date: date_t | str | None = None,
    *,
    limit: int = 1000,
    with_indicators: bool = False,
    indicator_names: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """读日线 + 可选追加技术指标，统一返回 JSON 可序列化 dict 列表。

    Args:
        with_indicators: True 时追加 ``indicator_names``（默认 MA + RSI + MACD）。
        indicator_names: 自定义指标列表，支持 ``"ma" / "rsi" / "macd" / "boll"``。
    """
    bars = get_daily_bars(db, stock_code, start_date, end_date, limit=limit)
    if not bars:
        return []

    df = _bars_to_df(bars)
    if with_indicators:
        df = apply_indicators(df, indicator_names)
        logger.debug(
            "computed indicators for %s: rows=%d cols=%s",
            stock_code, len(df), list(df.columns),
        )

    return [_row_to_item(row) for _, row in df.iterrows()]
