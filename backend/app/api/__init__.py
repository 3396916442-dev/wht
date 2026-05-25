"""聚合所有子路由，统一挂到 settings.API_PREFIX 下（默认 /api/v1）。

注意：根级 ``/health`` 由 ``app.main`` 直接定义，不在此聚合，
便于 k8s / docker healthcheck 探活。
"""

from fastapi import APIRouter

from app.api.backtest_api import router as backtest_router
from app.api.data_api import router as data_router
from app.api.stock_api import router as stock_router
from app.api.strategy_api import router as strategy_router

api_router = APIRouter()
api_router.include_router(stock_router)
api_router.include_router(data_router)
api_router.include_router(backtest_router)
api_router.include_router(strategy_router)
