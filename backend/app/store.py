"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。
计数口径不在本模块维护：概览统计统一委托给各模块服务，与列表取数走同一条路。
"""
from __future__ import annotations

from typing import Any

from app.catalog import MODULES
from app.seed import SEED_ROWS


class Store:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {
            name: [dict(row) for row in rows] for name, rows in SEED_ROWS.items()
        }

    def module_names(self) -> list[str]:
        return [spec.key for spec in MODULES]

    def rows(self, module: str) -> list[dict[str, Any]]:
        return self._tables.setdefault(module, [])

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

    def overview(self) -> dict[str, object]:
        # 延迟导入避免与 services.base 形成循环依赖；
        # 概览数字直接来自各模块服务的 module_summary，与模块列表同口径。
        from app.services.registry import get_service

        modules: list[dict[str, object]] = []
        for spec in MODULES:
            summary = get_service(spec.key).module_summary()
            modules.append({"name": spec.key, **summary})
        cards = [
            {"label": "业务模块", "value": len(modules)},
            {"label": "今日新增", "value": sum(int(item["created"]) for item in modules)},
            {"label": "待处理", "value": sum(int(item["pending"]) for item in modules)},
            {"label": "异常量", "value": sum(int(item["abnormal"]) for item in modules)},
        ]
        return {"cards": cards, "modules": modules}


store = Store()
