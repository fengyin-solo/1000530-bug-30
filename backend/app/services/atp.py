"""列车防护业务规则：状态流转、字段校验与筛选口径统一由 catalog + 服务基类维护。"""
from __future__ import annotations

from app.catalog import MODULE_SPECS
from app.services.base import ModuleService

# 模块固定口径（状态序列、动作、异常集合、统计卡片）的唯一出处
MODULE = "atp"
SPEC = MODULE_SPECS[MODULE]
STATUS_ORDER = list(SPEC.statuses)
ACTION_RULES = dict(SPEC.action_rules)
REQUIRED_FIELDS = list(SPEC.required_fields)


class AtpService(ModuleService):
    spec = SPEC
