"""AI 能力层。

第一版仅包含规则化的 :mod:`report_generator`（不调用大模型）。

后期会扩展：
    - 大模型复盘解读 / 选股
    - 新闻情绪分析
    - 因子挖掘 / 自动化策略生成

约定该层只对外暴露纯函数或 Service，不直接耦合具体大模型 SDK，
通过 ``providers/`` 子目录封装不同后端（OpenAI / Ollama / 通义 等）。
"""

from app.ai.report_generator import (
    DISCLAIMER,
    PROVIDER_NAME,
    generate_report,
)

__all__ = ["generate_report", "DISCLAIMER", "PROVIDER_NAME"]
