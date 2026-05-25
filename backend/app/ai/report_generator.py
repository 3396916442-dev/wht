"""回测报告生成器（第一版：规则化模板，**不调用大模型**）。

输入是 :func:`app.services.backtest_service.get_backtest_detail` 返回的 dict
（含 metrics / trades / equity_curve），输出是结构化中文报告。

设计为「provider 可替换」
========================
对外只暴露 :func:`generate_report(detail) -> dict`，未来要接 OpenAI / 通义 / Ollama 时：

    1. 在 ``app/ai/providers/`` 下加 ``openai_provider.py`` 等
    2. 让 :func:`generate_report` 根据 ``settings.AI_PROVIDER`` 选择 provider
    3. 调用方（API / service）签名不变

每个 section 含：
    - ``title``    分段标题
    - ``level``    info / good / warning / danger（前端着色）
    - ``content``  多行字符串列表
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

# ---- 常量 ---------------------------------------------------------------

LEVEL_INFO = "info"
LEVEL_GOOD = "good"
LEVEL_WARNING = "warning"
LEVEL_DANGER = "danger"

PROVIDER_NAME = "rule-based"

# 假设无风险年化（一年期定存 / 货币基金口径）
RISK_FREE_RATE = 0.03

DISCLAIMER = (
    "本报告由本平台基于历史回测数据规则化生成，仅供技术研究与个人学习参考，"
    "不构成任何形式的投资建议。市场有风险，投资需谨慎；过往表现不代表未来收益。"
    "请独立判断并自行承担投资风险。"
)


# ---- 主入口 -------------------------------------------------------------

def generate_report(detail: dict[str, Any]) -> dict[str, Any]:
    """根据回测结果生成结构化中文报告。

    Args:
        detail: ``get_backtest_detail`` 返回的 dict（含 task_id / metrics /
            trades / equity_curve / params 等）。

    Returns:
        ``{ task_id, stock_code, summary, sections: [...], disclaimer,
            generated_at, provider }``
    """
    metrics = detail.get("metrics") or {}
    trades = detail.get("trades") or []
    equity_curve = detail.get("equity_curve") or []

    sections: list[dict[str, Any]] = [
        _section_overall(detail, metrics, equity_curve),
        _section_returns(detail, metrics),
        _section_drawdown(metrics),
        _section_frequency(metrics, equity_curve),
        _section_winrate(metrics, trades),
        _section_overfit_warning(detail, metrics, equity_curve),
    ]

    return {
        "task_id": detail.get("task_id"),
        "stock_code": detail.get("stock_code"),
        "params": detail.get("params") or {},
        "summary": _build_summary(metrics),
        "sections": sections,
        "disclaimer": DISCLAIMER,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "provider": PROVIDER_NAME,
    }


# ---- 一句话总结 ---------------------------------------------------------

def _build_summary(metrics: dict[str, Any]) -> str:
    tr = metrics.get("total_return")
    md = metrics.get("max_drawdown")
    n = metrics.get("trade_count", 0)

    if tr is None:
        return "回测数据不足，无法形成结论。"

    if tr >= 0.10:
        verdict = "策略整体表现较好"
    elif tr > 0:
        verdict = "策略整体小幅盈利"
    elif tr > -0.10:
        verdict = "策略整体小幅亏损"
    else:
        verdict = "策略整体亏损明显"

    return (
        f"{verdict}：总收益 {_pct(tr)}，最大回撤 {_pct(md)}，共 {n} 笔交易。"
    )


# ---- Section 实现 -------------------------------------------------------

def _section_overall(detail: dict, metrics: dict, equity_curve: list) -> dict:
    days = len(equity_curve)
    code = detail.get("stock_code") or "—"
    start = detail.get("start_date") or "—"
    end = detail.get("end_date") or "—"
    initial = float(detail.get("initial_cash") or 0)
    params = detail.get("params") or {}
    short = params.get("short_window", "—")
    long_ = params.get("long_window", "—")

    tr = metrics.get("total_return")
    ar = metrics.get("annual_return")
    md = metrics.get("max_drawdown")
    sr = metrics.get("sharpe_ratio")
    n = metrics.get("trade_count", 0)
    final_value = initial * (1 + (tr or 0))

    lines = [
        f"标的：{code}；回测窗口：{start} ~ {end}（共 {days} 个交易日）。",
        f"策略参数：MA 双均线，short_window={short}，long_window={long_}。",
        f"初始资金：¥{initial:,.0f}，期末权益：¥{final_value:,.0f}。",
        (
            f"核心指标：总收益 {_pct(tr)}，年化 {_pct(ar)}，最大回撤 {_pct(md)}，"
            f"夏普 {_num(sr, 2)}，共发生 {n} 笔交易。"
        ),
    ]
    return {
        "title": "策略总体表现",
        "level": _level_for_total_return(tr),
        "content": lines,
    }


def _section_returns(detail: dict, metrics: dict) -> dict:
    tr = metrics.get("total_return")
    ar = metrics.get("annual_return")
    initial = float(detail.get("initial_cash") or 0)

    if tr is None:
        return {
            "title": "收益情况",
            "level": LEVEL_INFO,
            "content": ["回测样本不足，无法判断收益水平。"],
        }

    profit = initial * tr
    lines: list[str] = []

    # 总收益评价
    if tr >= 0.30:
        lines.append(f"总收益 {_pct(tr)} 处于极佳区间，明显跑赢一般理财产品。")
        level = LEVEL_GOOD
    elif tr >= 0.10:
        lines.append(f"总收益 {_pct(tr)} 表现亮眼，跑赢一年期定存（约 3% 假设）。")
        level = LEVEL_GOOD
    elif tr > 0:
        lines.append(f"总收益 {_pct(tr)} 小幅盈利，但相对市场平均水平仅勉强持平。")
        level = LEVEL_INFO
    elif tr > -0.10:
        lines.append(f"总收益 {_pct(tr)} 小幅亏损，需复盘是否存在频繁交易或滑点损耗。")
        level = LEVEL_WARNING
    else:
        lines.append(f"总收益 {_pct(tr)} 亏损明显，策略在该样本上不具盈利能力。")
        level = LEVEL_DANGER

    # 年化对比无风险
    if ar is not None:
        excess = ar - RISK_FREE_RATE
        if excess >= 0.05:
            lines.append(
                f"年化收益 {_pct(ar)}，相对无风险基准（{_pct(RISK_FREE_RATE)}）"
                f"超额收益约 {_pct(excess)}。"
            )
        elif excess >= 0:
            lines.append(
                f"年化收益 {_pct(ar)}，仅小幅跑赢无风险基准（{_pct(RISK_FREE_RATE)}）。"
            )
        else:
            lines.append(
                f"年化收益 {_pct(ar)}，未能跑赢无风险基准（{_pct(RISK_FREE_RATE)}），"
                f"持有者承担额外波动风险却未获得相应回报。"
            )

    sign = "+" if profit >= 0 else "-"
    lines.append(f"期末权益较初始资金变动：{sign}¥{abs(profit):,.0f}。")

    return {"title": "收益情况", "level": level, "content": lines}


def _section_drawdown(metrics: dict) -> dict:
    md = metrics.get("max_drawdown")

    if md is None:
        return {
            "title": "最大回撤风险",
            "level": LEVEL_INFO,
            "content": ["回测数据不足以计算回撤。"],
        }

    abs_md = abs(md)
    if abs_md < 0.05:
        verdict = "回撤极小，账面波动可控"
        level = LEVEL_GOOD
    elif abs_md < 0.15:
        verdict = "回撤可控，风险水平较低"
        level = LEVEL_INFO
    elif abs_md < 0.30:
        verdict = "回撤中等，需做好心理与仓位准备"
        level = LEVEL_WARNING
    else:
        verdict = "回撤较高，对持仓心理与资金管理是较大挑战"
        level = LEVEL_DANGER

    return {
        "title": "最大回撤风险",
        "level": level,
        "content": [
            f"回测期内最大回撤 {_pct(md)}，{verdict}。",
            f"含义：在最不利的时点持有该策略，账面浮亏一度达 {_pct(md)}。",
            "若实盘资金对回撤敏感（如杠杆 / 短期需用资金），应将该数值视作风险红线。",
        ],
    }


def _section_frequency(metrics: dict, equity_curve: list) -> dict:
    n = int(metrics.get("trade_count") or 0)
    days = len(equity_curve)

    if days <= 0:
        return {
            "title": "交易频率",
            "level": LEVEL_INFO,
            "content": ["回测样本不足，无法估算交易频率。"],
        }

    annualized = n / days * 252 if days > 0 else 0
    monthly = n / days * 21 if days > 0 else 0

    if n == 0:
        verdict = "全程未触发交易，可能是策略参数过于严格"
        level = LEVEL_WARNING
    elif annualized < 4:
        verdict = "极少交易（年均 < 4 次），样本量不足以充分检验策略"
        level = LEVEL_WARNING
    elif annualized < 24:
        verdict = "低频交易（年均 4 ~ 24 次），手续费与滑点拖累有限"
        level = LEVEL_GOOD
    elif annualized < 120:
        verdict = "中频交易（年均 24 ~ 120 次），需关注成本对收益的侵蚀"
        level = LEVEL_INFO
    else:
        verdict = "高频交易（年均 > 120 次），强烈建议精确测算交易成本"
        level = LEVEL_WARNING

    return {
        "title": "交易频率",
        "level": level,
        "content": [
            f"回测期间共 {n} 笔交易（{days} 个交易日，月均 {monthly:.1f} 次 / 年化 {annualized:.1f} 次）。",
            verdict + "。",
        ],
    }


def _section_winrate(metrics: dict, trades: list) -> dict:
    win_rate = metrics.get("win_rate")
    n = int(metrics.get("trade_count") or 0)
    closed_pairs = n // 2  # 一对 BUY+SELL 算一笔完整交易

    if win_rate is None or closed_pairs == 0:
        return {
            "title": "胜率评价",
            "level": LEVEL_INFO,
            "content": [
                "未发生完整的「买入 → 卖出」配对，胜率指标不可用。",
                "建议适度延长回测窗口或调整策略参数，让交易能够走完一个完整持仓周期。",
            ],
        }

    if win_rate >= 0.6:
        verdict = "胜率较高，盈利交易占多数"
        level = LEVEL_GOOD
    elif win_rate >= 0.5:
        verdict = "胜率中等，盈亏交易接近持平"
        level = LEVEL_INFO
    else:
        verdict = "胜率偏低，多数交易亏损"
        level = LEVEL_WARNING

    return {
        "title": "胜率评价",
        "level": level,
        "content": [
            f"已闭合的完整交易约 {closed_pairs} 笔，胜率 {_pct(win_rate)}。",
            verdict + "。",
            "提示：胜率仅反映「盈/亏次数比例」，并不直接等于赚不赚钱；"
            "盈亏比（单笔平均盈利 / 单笔平均亏损）同样关键，第一版报告未给出，后续版本会补充。",
        ],
    }


def _section_overfit_warning(detail: dict, metrics: dict, equity_curve: list) -> dict:
    """过拟合提醒：多条件累加，命中越多越值得警惕。"""
    warnings: list[str] = []
    days = len(equity_curve)
    n = int(metrics.get("trade_count") or 0)
    tr = metrics.get("total_return")
    sr = metrics.get("sharpe_ratio")
    md = metrics.get("max_drawdown")
    params = detail.get("params") or {}
    long_window = params.get("long_window")

    # R1：高收益但样本极少
    if n < 4 and tr is not None and tr > 0.20:
        warnings.append(
            f"交易次数仅 {n} 笔但总收益高达 {_pct(tr)}，结果由极少样本主导，"
            "稳定性存疑，建议扩大回测窗口验证。"
        )

    # R2：夏普异常高
    if sr is not None and sr > 5:
        warnings.append(
            f"夏普比率 {_num(sr, 2)} 异常之高，常见于参数过拟合 / 数据偏差 / 未来函数泄漏，"
            "需检查是否存在 look-ahead bias。"
        )

    # R3：回撤过小但收益显著
    if md is not None and tr is not None and abs(md) < 0.02 and tr > 0.20:
        warnings.append(
            f"最大回撤仅 {_pct(md)} 而总收益 {_pct(tr)}，回撤偏小可能源于回测期内单边行情，"
            "换样本期可能表现迥异。"
        )

    # R4：策略窗口与回测周期比例过大
    if isinstance(long_window, int) and days > 0 and long_window > days / 3:
        warnings.append(
            f"long_window={long_window} 占回测总长 {days} 的比例超过 1/3，"
            "策略实际有效信号区间较短，参数自由度不足。"
        )

    # R5：长期持有未交易（trade_count == 0），实质是 buy-and-hold 假象
    if n == 0 and tr is not None:
        warnings.append(
            "策略全程未触发交易，回测结果等同「持币不动」，"
            "看上去的收益完全是标的本身的涨跌，与策略无关。"
        )

    if not warnings:
        return {
            "title": "过拟合 / 数据陷阱提醒",
            "level": LEVEL_INFO,
            "content": [
                "本次回测未发现明显的过拟合特征。仍建议至少在 2 个不同样本期 / 标的上做交叉验证，"
                "避免参数仅在历史区间表现良好。",
            ],
        }

    level = LEVEL_DANGER if len(warnings) >= 2 else LEVEL_WARNING
    return {
        "title": "过拟合 / 数据陷阱提醒",
        "level": level,
        "content": warnings + [
            "推荐做法：在不同股票 / 不同时间区间做样本外验证，必要时引入 walk-forward 测试。",
        ],
    }


# ---- 工具 ---------------------------------------------------------------

def _pct(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.{digits}f}%"


def _num(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}"


def _level_for_total_return(tr: float | None) -> str:
    if tr is None:
        return LEVEL_INFO
    if tr >= 0.10:
        return LEVEL_GOOD
    if tr >= 0:
        return LEVEL_INFO
    if tr >= -0.10:
        return LEVEL_WARNING
    return LEVEL_DANGER


__all__ = ["generate_report", "DISCLAIMER", "PROVIDER_NAME"]
