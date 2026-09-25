"""模块服务注册表：按 catalog 台账生成各模块服务，概览与路由共用同一实例。"""
from __future__ import annotations

from app.catalog import MODULE_SPECS, ModuleSpec
from app.services.base import ModuleService


def _make_service(spec: ModuleSpec) -> type[ModuleService]:
    return type(f"{spec.key.title()}Service", (ModuleService,), {"spec": spec})


_SERVICES: dict[str, ModuleService] = {
    key: _make_service(spec)() for key, spec in MODULE_SPECS.items()
}


def get_service(module: str) -> ModuleService:
    return _SERVICES[module]
