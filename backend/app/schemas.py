"""接口出入参模型：列表分页、动作结果与登记载荷。

各模块明细都是动态字段字典，不再为每个模块维护一份静态字段模型，
字段口径统一以 app/catalog.py 为准。
"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class StatItem(BaseModel):
    """模块页顶部统计卡片：label 与前端卡片文案保持一致。"""

    label: str
    value: int = 0


class PageResult(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    size: int = 20
    # 与列表同一次请求返回的模块统计卡片，保证卡片和表格同源
    stats: list[StatItem] = Field(default_factory=list)


class ActionResult(BaseModel):
    ok: bool
    message: str
    entry: dict[str, Any] | None = None


class EntryPayload(BaseModel):
    """登记或修改一条业务记录时提交的字段集合。"""

    values: dict[str, Any] = Field(default_factory=dict)
    remark: str | None = None
