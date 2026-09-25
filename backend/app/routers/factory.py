"""路由工厂：各业务模块的接口形状完全一致，统一在这里生成。

概览与列表共用 services 里的同一套取数口径；列表响应额外带上 ``stats``，
模块页顶部的统计卡片与表格数据同源，不再出现各算各的情况。
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.catalog import ModuleSpec
from app.schemas import ActionResult, EntryPayload, PageResult
from app.services.registry import get_service


def build_router(spec: ModuleSpec) -> APIRouter:
    router = APIRouter(prefix=f"/api/{spec.key}", tags=[spec.label])
    service = get_service(spec.key)
    status_text = "、".join(spec.statuses)

    @router.get("", response_model=PageResult[dict])
    def list_entries(
        keyword: str | None = Query(default=None, description=f"按{spec.keyword_field}检索"),
        status: str | None = Query(default=None, description=status_text),
        page: int = 1,
        size: int = 20,
    ) -> PageResult[dict]:
        """按关键字与状态过滤模块列表；没有数据时返回空页，不报错。

        空字符串与未传等价（前端空输入框会序列化成 keyword=&status=）。
        """
        if size > 200:
            raise HTTPException(status_code=400, detail="每页最多 200 条，请缩小分页范围")
        items, total = service.list_entries(keyword=keyword, status=status, page=page, size=size)
        # 列表与卡片同一次请求返回，卡片口径来自未筛选的全量列表
        return PageResult(
            items=items,
            total=total,
            page=page,
            size=size,
            stats=service.module_stats(),
        )

    # 注意：/export 必须在 /{entry_id} 之前注册，否则会被当成 entry_id
    @router.get("/export")
    def export_entries() -> dict[str, Any]:
        """导出模块清单：返回未过滤的全量数据。"""
        items, total = service.list_entries(page=1, size=10000)
        return {"module": spec.key, "total": total, "items": items}

    @router.get("/{entry_id}", response_model=dict)
    def get_entry(entry_id: int) -> dict[str, Any]:
        """读取单条明细；不存在时给出可读的错误说明。"""
        entry = service.get_entry(entry_id)
        if entry is None:
            raise HTTPException(status_code=404, detail=f"{spec.entity} {entry_id} 不存在或已归档")
        return entry

    @router.post("", response_model=ActionResult)
    def create_entry(payload: EntryPayload) -> ActionResult:
        """登记一条记录，缺字段时说明原因而不是静默丢弃。"""
        entry, missing = service.create_entry(payload.values)
        if missing:
            return ActionResult(ok=False, message=f"缺少必填字段：{'、'.join(missing)}")
        return ActionResult(ok=True, message=f"{spec.entity}已登记", entry=entry)

    @router.post("/{entry_id}/actions", response_model=ActionResult)
    def run_action(entry_id: int, payload: EntryPayload) -> ActionResult:
        """对单条记录执行模块允许的动作；不允许的动作会被拦下并说明原因。"""
        action = str(payload.values.get("action") or "").strip()
        entry, message = service.run_action(entry_id, action)
        if entry is None:
            return ActionResult(ok=False, message=message)
        return ActionResult(ok=True, message=message, entry=entry)

    return router
