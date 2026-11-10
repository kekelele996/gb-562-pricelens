"""路由聚合：统一 /api 前缀（Nginx 反代时剥掉 /api）。"""
from fastapi import APIRouter

from src.routes.alerts import router as alerts_router
from src.routes.auth import router as auth_router
from src.routes.health import router as health_router
from src.routes.reports import router as reports_router
from src.routes.runs import router as runs_router
from src.routes.sites import router as sites_router
from src.routes.snapshots import router as snapshots_router
from src.routes.templates import router as templates_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(sites_router)
api_router.include_router(templates_router)
api_router.include_router(snapshots_router)
api_router.include_router(runs_router)
api_router.include_router(alerts_router)
api_router.include_router(reports_router)
