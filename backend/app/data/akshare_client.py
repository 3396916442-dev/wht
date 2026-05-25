"""akshare A 股数据客户端。

只负责"调用外部数据源 → 列名/类型标准化 → 返回普通 dict 列表"，
不直接读写数据库；后续要兼容 tushare 时只需加一个同接口的 ``tushare_client``。

字段映射策略
============

akshare 返回的是 **中文列名**，且不同版本可能新增 / 调整列。本模块的策略：

1. 把所有 akshare 返回的中文列名集中作为 **常量** 维护
   （:class:`_AkshareDailyColumns`），版本升级出现改名时只动这一处。
2. 严格区分 **必需列**（缺失 → ``AkshareError``，附带实际列名做诊断）与
   **可选列**（缺失 → 字段填 ``None``）。
3. **rename 之前** 先做"中文列存在性预校验"，错误信息直接告诉调用方
   缺了哪个、实际返回了哪些列；不依赖 rename 后的英文名。
4. 列名先 ``strip()``，避免 akshare 偶发的前后空格导致漏匹配。
5. 未在映射中的列直接 **丢弃**（例如未来可能新增的"股票代码"列），
   避免污染下游 ORM。

akshare 当前实测列（``ak.stock_zh_a_hist``）：
    日期 / 股票代码 / 开盘 / 收盘 / 最高 / 最低 / 成交量 / 成交额 /
    振幅 / 涨跌幅 / 涨跌额 / 换手率

单位：成交量"手"（1 手 = 100 股），成交额"元"，振幅/涨跌幅/换手率"%"。
本模块全部保持原始单位。
"""

from __future__ import annotations

import logging
import os
import json
from contextlib import contextmanager
from datetime import date as date_t
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
import requests

from app.core.config import settings

logger = logging.getLogger("quant.akshare")

_PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)

_EM_DAILY_COLUMNS = [
    "日期",
    "开盘",
    "收盘",
    "最高",
    "最低",
    "成交量",
    "成交额",
    "振幅",
    "涨跌幅",
    "涨跌额",
    "换手率",
    "股票代码",
]


class AkshareError(RuntimeError):
    """akshare 调用 / 解析失败时抛出。"""


# ---- akshare 中文列名常量 ----------------------------------------------

class _AkshareDailyColumns:
    """``ak.stock_zh_a_hist`` 返回 DataFrame 的中文列名常量。

    akshare 升级若改列名，统一在此处更新。
    """

    DATE = "日期"
    STOCK_CODE = "股票代码"   # akshare 新版本会带，本模块不使用，保留作识别
    OPEN = "开盘"
    CLOSE = "收盘"
    HIGH = "最高"
    LOW = "最低"
    VOLUME = "成交量"          # 单位：手
    AMOUNT = "成交额"          # 单位：元
    AMPLITUDE = "振幅"         # 单位：%（暂不入库）
    PCT_CHANGE = "涨跌幅"       # 单位：%
    PRICE_CHANGE = "涨跌额"    # 单位：元（暂不入库）
    TURNOVER = "换手率"        # 单位：%


# 中文列名 → 我们 daily_bars 表字段
_COLUMN_MAP: dict[str, str] = {
    _AkshareDailyColumns.DATE: "trade_date",
    _AkshareDailyColumns.OPEN: "open",
    _AkshareDailyColumns.CLOSE: "close",
    _AkshareDailyColumns.HIGH: "high",
    _AkshareDailyColumns.LOW: "low",
    _AkshareDailyColumns.VOLUME: "volume",
    _AkshareDailyColumns.AMOUNT: "amount",
    _AkshareDailyColumns.PCT_CHANGE: "pct_change",
    _AkshareDailyColumns.TURNOVER: "turnover",
}

# 必需列：akshare 必须返回（缺一即视为接口异常）
_REQUIRED_COLUMNS: frozenset[str] = frozenset({
    _AkshareDailyColumns.DATE,
    _AkshareDailyColumns.OPEN,
    _AkshareDailyColumns.CLOSE,
    _AkshareDailyColumns.HIGH,
    _AkshareDailyColumns.LOW,
    _AkshareDailyColumns.VOLUME,
    _AkshareDailyColumns.AMOUNT,
})

# 可选列：缺失则对应字段填 None
_OPTIONAL_COLUMNS: frozenset[str] = frozenset({
    _AkshareDailyColumns.PCT_CHANGE,
    _AkshareDailyColumns.TURNOVER,
})


# ---- 网络请求 -----------------------------------------------------------

@contextmanager
def _isolated_proxy_env(use_system_proxy: bool):
    """临时清理环境代理变量，避免 requests 误读 Shell 代理。"""
    if use_system_proxy:
        yield
        return
    saved = {key: os.environ.pop(key, None) for key in _PROXY_ENV_KEYS}
    try:
        yield
    finally:
        for key, value in saved.items():
            if value is not None:
                os.environ[key] = value


def _build_requests_session() -> requests.Session:
    """构造 akshare / 东方财富请求 Session。

    默认 ``trust_env=False`` 且显式 ``proxies=None``，绕过 macOS 系统代理
    （常见于 Clash 关闭后仍残留 127.0.0.1:789x 导致 ProxyError）。
    """
    session = requests.Session()
    session.trust_env = settings.AKSHARE_USE_SYSTEM_PROXY
    if settings.AKSHARE_HTTP_PROXY:
        proxy = settings.AKSHARE_HTTP_PROXY.strip()
        session.proxies = {"http": proxy, "https": proxy}
    elif not settings.AKSHARE_USE_SYSTEM_PROXY:
        session.proxies = {"http": None, "https": None}
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://quote.eastmoney.com/",
        }
    )
    return session


def _proxy_hint(exc: Exception) -> str:
    if "ProxyError" in type(exc).__name__ or "proxy" in str(exc).lower():
        return (
            "；检测到代理相关错误：请确认 Clash/V2Ray 已启动，"
            "或在 backend/.env 设置 AKSHARE_HTTP_PROXY=http://127.0.0.1:7890；"
            "若无需代理请保持 AKSHARE_USE_SYSTEM_PROXY=false"
        )
    return ""


def _fetch_em_daily_df(
    session: requests.Session,
    stock_code: str,
    start: str,
    end: str,
    adjust: str,
    timeout: int,
) -> pd.DataFrame:
    """直接请求东方财富日线接口，返回与 akshare 一致的中文列 DataFrame。"""
    market_code = 1 if stock_code.startswith("6") else 0
    adjust_dict = {"qfq": "1", "hfq": "2", "": "0"}
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
        "klt": "101",
        "fqt": adjust_dict.get(adjust, "0"),
        "secid": f"{market_code}.{stock_code}",
        "beg": start,
        "end": end,
    }
    response = session.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    data_json = response.json()
    klines = (
        data_json.get("data", {}).get("klines")
        if isinstance(data_json.get("data"), dict)
        else None
    )
    if not klines:
        return pd.DataFrame()

    df = pd.DataFrame([item.split(",") for item in klines])
    df[_AkshareDailyColumns.STOCK_CODE] = stock_code
    df.columns = _EM_DAILY_COLUMNS
    return df


def _to_tx_symbol(stock_code: str) -> str:
    if stock_code.startswith("6"):
        return f"sh{stock_code}"
    if stock_code.startswith(("0", "3")):
        return f"sz{stock_code}"
    return f"bj{stock_code}"


def _fetch_tx_daily_df(
    session: requests.Session,
    stock_code: str,
    start: str,
    end: str,
    adjust: str,
    timeout: int,
) -> pd.DataFrame:
    """腾讯证券备用数据源（东方财富不可达时使用）。"""
    tx_symbol = _to_tx_symbol(stock_code)
    url = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
    start_year = int(start[:4])
    end_year = int(end[:4])
    frames: list[pd.DataFrame] = []

    for year in range(start_year, end_year + 1):
        params = {
            "_var": f"kline_day{adjust}{year}",
            "param": f"{tx_symbol},day,{year}-01-01,{year + 1}-12-31,640,{adjust}",
            "r": "0.8205512681390605",
        }
        response = session.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        text = response.text
        payload_start = text.find("={") + 1
        if payload_start <= 0:
            continue

        data_json = json.loads(text[payload_start:])
        data_block = data_json.get("data")
        if not isinstance(data_block, dict):
            continue

        symbol_data = data_block.get(tx_symbol)
        if not isinstance(symbol_data, dict):
            continue

        if "day" in symbol_data:
            raw = symbol_data["day"]
        elif adjust == "hfq" and "hfqday" in symbol_data:
            raw = symbol_data["hfqday"]
        elif "qfqday" in symbol_data:
            raw = symbol_data["qfqday"]
        else:
            continue

        if not raw:
            continue

        temp = pd.DataFrame(raw).iloc[:, :6]
        temp.columns = [
            _AkshareDailyColumns.DATE,
            _AkshareDailyColumns.OPEN,
            _AkshareDailyColumns.CLOSE,
            _AkshareDailyColumns.HIGH,
            _AkshareDailyColumns.LOW,
            _AkshareDailyColumns.AMOUNT,
        ]
        frames.append(temp)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df[_AkshareDailyColumns.DATE] = pd.to_datetime(
        df[_AkshareDailyColumns.DATE], errors="coerce"
    ).dt.date
    df = df.dropna(subset=[_AkshareDailyColumns.DATE])
    start_d = pd.to_datetime(start, format="%Y%m%d").date()
    end_d = pd.to_datetime(end, format="%Y%m%d").date()
    df = df[(df[_AkshareDailyColumns.DATE] >= start_d) & (df[_AkshareDailyColumns.DATE] <= end_d)]
    df = df.drop_duplicates(subset=[_AkshareDailyColumns.DATE], ignore_index=True)

    # 腾讯源无成交量字段，用 0 占位以满足入库必需列
    df[_AkshareDailyColumns.VOLUME] = 0
    df[_AkshareDailyColumns.PCT_CHANGE] = None
    df[_AkshareDailyColumns.TURNOVER] = None
    return df[
        [
            _AkshareDailyColumns.DATE,
            _AkshareDailyColumns.OPEN,
            _AkshareDailyColumns.CLOSE,
            _AkshareDailyColumns.HIGH,
            _AkshareDailyColumns.LOW,
            _AkshareDailyColumns.VOLUME,
            _AkshareDailyColumns.AMOUNT,
            _AkshareDailyColumns.PCT_CHANGE,
            _AkshareDailyColumns.TURNOVER,
        ]
    ]


# ---- 工具函数 -----------------------------------------------------------

def _to_akshare_date(value: str | date_t) -> str:
    """规整为 akshare 要求的 ``YYYYMMDD``。"""
    if isinstance(value, date_t):
        return value.strftime("%Y%m%d")
    if isinstance(value, str):
        s = value.replace("-", "").replace("/", "")
        if len(s) != 8 or not s.isdigit():
            raise ValueError(f"无效日期：{value!r}（期望 YYYY-MM-DD 或 YYYYMMDD）")
        return s
    raise TypeError(f"unsupported date type: {type(value).__name__}")


def _to_decimal(value: Any) -> Decimal | None:
    if value is None or pd.isna(value):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise AkshareError(f"无法解析为 Decimal：{value!r} ({exc})") from exc


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """对 akshare 返回的 DataFrame 做列校验 + 标准化。

    步骤：
        1. 列名 ``strip()``
        2. 必需中文列存在性校验
        3. 仅保留我们认识的列（必需 + 可选），其它列丢弃
        4. 中文 → 英文 rename

    Raises:
        AkshareError: 必需列缺失，错误信息含实际列与缺失列对比。
    """
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    actual = set(df.columns)
    missing_required = _REQUIRED_COLUMNS - actual
    if missing_required:
        raise AkshareError(
            "akshare 返回缺少必需列："
            f"{sorted(missing_required)}；实际返回列：{sorted(actual)}"
        )

    # 只保留我们认识的列；先存在性过滤，再 rename
    relevant_zh = [zh for zh in _COLUMN_MAP if zh in actual]
    df = df[relevant_zh].rename(columns=_COLUMN_MAP)

    # 提示一下被丢弃的未知列，便于发现 akshare 升级新增字段
    dropped = actual - set(_COLUMN_MAP.keys())
    if dropped:
        logger.debug("dropped unknown columns from akshare: %s", sorted(dropped))

    return df


# ---- 主函数 -------------------------------------------------------------

def fetch_stock_daily_from_akshare(
    stock_code: str,
    start_date: str | date_t,
    end_date: str | date_t,
    *,
    adjust: str = "",
) -> list[dict[str, Any]]:
    """从 akshare 拉取 A 股日线行情。

    Args:
        stock_code: 不带前缀的股票代码（如 ``"600519"`` / ``"000001"``）。
        start_date / end_date: 日期，``date`` 或 ``"YYYY-MM-DD"`` / ``"YYYYMMDD"``。
        adjust: ``""``（默认不复权）/ ``"qfq"`` 前复权 / ``"hfq"`` 后复权。

    Returns:
        标准化字典列表，每条形如::

            {
                "stock_code": "600519",
                "trade_date": date(2024, 1, 2),
                "open": Decimal("1700.000"),
                "high": Decimal("1720.000"),
                "low":  Decimal("1690.000"),
                "close":Decimal("1710.500"),
                "volume": 12345,                # 单位：手
                "amount": Decimal("21000000.00"),
                "pct_change": Decimal("0.6500") | None,   # 可选列缺失则 None
                "turnover":   Decimal("0.1200") | None,
            }

        akshare 返回空 → 返回空列表（不抛错）。

    Raises:
        AkshareError: 调用失败 / 必需列缺失 / 单元格解析失败。
        ValueError:   入参日期格式非法。
    """
    start = _to_akshare_date(start_date)
    end = _to_akshare_date(end_date)

    logger.info(
        "fetch akshare daily: stock=%s start=%s end=%s adjust=%s",
        stock_code, start, end, adjust or "none",
    )

    timeout = settings.AKSHARE_TIMEOUT
    df: pd.DataFrame | None = None
    last_exc: Exception | None = None

    with _isolated_proxy_env(settings.AKSHARE_USE_SYSTEM_PROXY):
        session = _build_requests_session()
        try:
            df = _fetch_em_daily_df(session, stock_code, start, end, adjust, timeout)
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "eastmoney fetch failed for %s, try tencent fallback: %s",
                stock_code,
                exc,
            )
            try:
                df = _fetch_tx_daily_df(session, stock_code, start, end, adjust, timeout)
            except Exception as tx_exc:
                last_exc = tx_exc
                logger.exception("akshare call failed for %s", stock_code)
                raise AkshareError(
                    f"akshare 调用失败：{tx_exc}{_proxy_hint(tx_exc)}"
                ) from tx_exc

    if df is None:
        raise AkshareError(
            f"akshare 调用失败：{last_exc}{_proxy_hint(last_exc or Exception())}"
        ) from last_exc

    if df is None or df.empty:
        logger.warning("akshare returned empty for %s [%s, %s]", stock_code, start, end)
        return []

    # 中文列校验 + 标准化 → 此后已是英文列名
    df = _normalize_columns(df)

    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        try:
            ts = pd.to_datetime(r["trade_date"]).date()
            rows.append(
                {
                    "stock_code": stock_code,
                    "trade_date": ts,
                    "open": _to_decimal(r["open"]),
                    "high": _to_decimal(r["high"]),
                    "low": _to_decimal(r["low"]),
                    "close": _to_decimal(r["close"]),
                    "volume": int(r["volume"]),
                    "amount": _to_decimal(r["amount"]),
                    # 可选列：标准化后若该列不存在则 .get 返回 None
                    "pct_change": _to_decimal(r.get("pct_change")),
                    "turnover": _to_decimal(r.get("turnover")),
                }
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise AkshareError(f"解析 akshare 行失败：{r.to_dict()} ({exc})") from exc

    logger.info("fetched %d rows for %s", len(rows), stock_code)
    return rows
