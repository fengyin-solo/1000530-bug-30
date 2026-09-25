"""业务服务基类：列表筛选、待处理/异常计数、状态流转全部走同一套口径。

概览接口通过同一份 ``query`` / ``module_summary`` 取数，保证“概览看到的待处理量”
和“点进模块列表能查到的条目数”永远一致。
"""
from __future__ import annotations

from typing import Any

from app.catalog import ModuleSpec
from app.store import store


def _normalize(value: str | None) -> str | None:
    """前端空输入框会序列化成 keyword=&status=，空串等价于“没传”。"""
    if value is None:
        return None
    value = value.strip()
    return value or None


class ModuleService:
    """所有模块服务的基类；差异部分全部由 catalog 的 ModuleSpec 描述。"""

    spec: ModuleSpec

    def query(self, *, keyword: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        """统一筛选口径：与概览计数共用，列表和概览不会再出现两套数。"""
        keyword = _normalize(keyword)
        status = _normalize(status)
        rows = store.rows(self.spec.key)
        if keyword:
            rows = [row for row in rows if keyword in str(row.get(self.spec.keyword_field, ""))]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        return rows

    def list_entries(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = self.query(keyword=keyword, status=status)
        total = len(rows)
        start = max(page - 1, 0) * size
        return rows[start:start + size], total

    def module_summary(self) -> dict[str, int]:
        """模块在概览里的计数：对未筛选的全量列表按状态口径统计。"""
        rows = store.rows(self.spec.key)
        return {
            "created": len(rows),
            "pending": sum(1 for row in rows if self.spec.is_pending(row.get("status"))),
            "abnormal": sum(1 for row in rows if self.spec.is_abnormal(row.get("status"))),
        }

    def module_stats(self) -> list[dict[str, Any]]:
        """模块页顶部统计卡片：取数同样来自未筛选的模块列表。"""
        rows = store.rows(self.spec.key)
        return [
            {"label": item.label, "value": self.spec.stat_value(item.rule, rows)}
            for item in self.spec.stats
        ]

    def get_entry(self, entry_id: int) -> dict[str, Any] | None:
        return store.find(self.spec.key, entry_id)

    def create_entry(self, values: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
        missing = [field for field in self.spec.required_fields if not str(values.get(field) or "").strip()]
        if missing:
            return None, missing
        rows = store.rows(self.spec.key)
        entry: dict[str, Any] = {"id": max((int(row.get("id", 0)) for row in rows), default=0) + 1}
        entry.update({field: values.get(field) for field in self.spec.required_fields})
        entry["status"] = self.spec.statuses[0]
        rows.append(self.spec.decorate(entry))
        return entry, []

    def run_action(self, entry_id: int, action: str) -> tuple[dict[str, Any] | None, str]:
        entry = store.find(self.spec.key, entry_id)
        if entry is None:
            return None, f"{self.spec.entity} {entry_id} 不存在或已归档"
        if action not in self.spec.action_rules:
            return None, f"动作「{action}」不属于{self.spec.label}可执行范围"
        target = self.spec.action_rules[action]
        if target not in self.spec.statuses:
            return None, f"目标状态「{target}」不在允许的状态序列里"
        entry["status"] = target
        self.spec.decorate(entry)
        return entry, f"{self.spec.entity}已{action}"
