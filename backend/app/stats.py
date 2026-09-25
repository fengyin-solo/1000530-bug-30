"""统计口径：运营概览卡片与各模块页面的统计卡片共用同一套计算规则。

每个模块用 (标签, 口径, 字段, 参数) 四元组声明自己的统计项，evaluate_stats
统一把规则跑在该模块的真实记录上。数字只在这里算一次，概览和模块页看到的是
同一份结果，不会再各算各的。
"""
from __future__ import annotations

from datetime import date
from typing import Any, Iterator

Row = dict[str, Any]
StatRule = tuple[str, str, str, Any]


def _numbers(rows: list[Row], field: str) -> Iterator[float]:
    """取出某字段里能解析成数字的值；样例数据里的占位文本直接跳过。"""
    for row in rows:
        try:
            yield float(str(row.get(field, "")).strip())
        except (TypeError, ValueError):
            continue


def evaluate_stats(rows: list[Row], rules: list[StatRule]) -> list[dict[str, Any]]:
    today = date.today().isoformat()
    month = today[:7]
    cards: list[dict[str, Any]] = []
    for label, kind, field, arg in rules:
        value: float
        if kind == "status":  # 某个状态条数
            value = sum(1 for row in rows if row.get("status") == arg)
        elif kind == "today":  # 日期字段落在今天
            value = sum(1 for row in rows if str(row.get(field) or "")[:10] == today)
        elif kind == "month":  # 日期字段落在本月
            value = sum(1 for row in rows if str(row.get(field) or "")[:7] == month)
        elif kind == "sum":  # 数值字段求和
            value = sum(_numbers(rows, field))
        elif kind == "avg":  # 数值字段取均值，没有可解析的值时为 0
            nums = list(_numbers(rows, field))
            value = round(sum(nums) / len(nums), 1) if nums else 0
        elif kind == "contains":  # 字段包含指定文本
            value = sum(1 for row in rows if str(arg) in str(row.get(field) or ""))
        elif kind == "distinct":  # 字段去重后的非空取值数
            value = len({str(row.get(field)).strip() for row in rows if str(row.get(field) or "").strip()})
        elif kind == "nonempty":  # 字段非空的条数
            value = sum(1 for row in rows if str(row.get(field) or "").strip())
        elif kind == "percent":  # 目标状态占指定状态集合的百分比
            hit, scope = arg
            total = sum(1 for row in rows if row.get("status") in scope)
            value = round(100 * sum(1 for row in rows if row.get("status") == hit) / total) if total else 0
        else:
            raise ValueError(f"未知统计口径：{kind}")
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        cards.append({"label": label, "value": value})
    return cards
