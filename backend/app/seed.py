"""示例数据：按模块台账确定性生成，任何环境启动后得到的都是同一组数据。

每个模块固定 3 条记录，状态依次取台账状态序列的前三个：
第 1 条初始态、第 2 条中间态、第 3 条也是非末态（业务仍在流转）。
``pending`` / ``abnormal`` 不手写，统一由状态按 catalog 的口径推导，
概览和模块列表因此永远不会对不上。
"""
from __future__ import annotations

from typing import Any

from app.catalog import MODULES, ModuleSpec

SEED_SIZE = 3  # 每个模块的示例记录条数，固定值，保证跨环境数字一致


def _seed_row(spec: ModuleSpec, index: int) -> dict[str, Any]:
    """生成第 index 条（从 1 开始）示例记录。"""
    status = spec.statuses[index - 1]
    row: dict[str, Any] = {
        "id": index,
        "status": status,
    }
    for field in spec.fields:
        if field in ("应答器数量", "领用数量"):
            # 仅有的两个数值字段：给确定的整数值，不要写成样例字符串
            row[field] = index * 10
            continue
        if field in ("投运日期", "转换时间", "计划日期", "开始时间", "完成时间", "发生时间",
                     "恢复时间", "领用日期", "巡视日期", "计划时段", "实际时段", "触发时间",
                     "验收日期", "交接时间"):
            row[field] = f"2026-09-{index:02d}"
            continue
        row[field] = f"{spec.label}样例{index}"
    # 编码类字段用模块前缀生成，保留原先 SECT-0001 这种可检索形态
    row[spec.fields[0]] = f"{spec.code_prefix}-{index:04d}"
    return spec.decorate(row)


def _build_seed_rows() -> dict[str, list[dict[str, Any]]]:
    return {
        spec.key: [_seed_row(spec, index) for index in range(1, SEED_SIZE + 1)]
        for spec in MODULES
    }


SEED_ROWS: dict[str, list[dict[str, Any]]] = _build_seed_rows()
