"""策略相关接口（占位）。

策略元信息以"代码内注册"为主、数据库为辅；
列表接口未来将合并：内置策略（代码注册） + 用户自定义策略（DB）。
"""

from fastapi import APIRouter

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("", summary="策略列表（占位）")
async def list_strategies() -> dict:
    return {"items": [], "total": 0, "detail": "to be implemented"}


@router.get("/{name}", summary="策略详情（占位）")
async def get_strategy(name: str) -> dict:
    return {"name": name, "detail": "to be implemented"}
