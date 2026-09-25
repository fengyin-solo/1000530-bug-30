"""状态评估接口：由统一路由工厂生成，取数口径与概览及其他模块保持一致。"""
from __future__ import annotations

from app.catalog import MODULE_SPECS
from app.routers.factory import build_router

router = build_router(MODULE_SPECS["assess"])
