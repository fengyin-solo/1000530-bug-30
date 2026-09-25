"""业务模块路由汇总：按 catalog 台账顺序统一注册。"""
from __future__ import annotations

from importlib import import_module

from app.catalog import MODULE_ORDER

ROUTERS = [import_module(f"app.routers.{name}") for name in MODULE_ORDER]
