"""运营概览聚合：概览卡片、模块汇总与模块页统计卡片唯一的取数来源。

每个模块的计数都通过该模块自己的 service（也就是列表接口背后的同一套逻辑）
拿到，概览数字和模块列表永远对得上；新增模块时往 SERVICES 里登记一处即可。
"""
from __future__ import annotations

from typing import Any

from app.services import alarm as svc_alarm
from app.services import assess as svc_assess
from app.services import atp as svc_atp
from app.services import dispose as svc_dispose
from app.services import fault as svc_fault
from app.services import interlock as svc_interlock
from app.services import measure as svc_measure
from app.services import patrol as svc_patrol
from app.services import plan as svc_plan
from app.services import section as svc_section
from app.services import shift as svc_shift
from app.services import signal as svc_signal
from app.services import spare as svc_spare
from app.services import switch as svc_switch
from app.services import task as svc_task
from app.services import track as svc_track
from app.services import verify as svc_verify
from app.services import window as svc_window

SERVICES: dict[str, Any] = {
    "section": svc_section.SectionService(),
    "signal": svc_signal.SignalService(),
    "switch": svc_switch.SwitchService(),
    "track": svc_track.TrackService(),
    "interlock": svc_interlock.InterlockService(),
    "atp": svc_atp.AtpService(),
    "plan": svc_plan.PlanService(),
    "task": svc_task.TaskService(),
    "fault": svc_fault.FaultService(),
    "dispose": svc_dispose.DisposeService(),
    "spare": svc_spare.SpareService(),
    "measure": svc_measure.MeasureService(),
    "patrol": svc_patrol.PatrolService(),
    "window": svc_window.WindowService(),
    "alarm": svc_alarm.AlarmService(),
    "verify": svc_verify.VerifyService(),
    "shift": svc_shift.ShiftService(),
    "assess": svc_assess.AssessService(),
}


def build_overview() -> dict[str, Any]:
    modules: list[dict[str, Any]] = []
    for name in sorted(SERVICES):
        service = SERVICES[name]
        # 与列表接口、导出接口走同一个 service 方法，口径天然一致
        rows, total = service.list_entries(page=1, size=10000)
        modules.append({
            "name": name,
            "created": total,
            "pending": sum(1 for row in rows if row.get("pending")),
            "abnormal": sum(1 for row in rows if row.get("abnormal")),
            "stats": service.stats(),
        })
    cards = [
        {"label": "业务模块", "value": len(modules)},
        {"label": "今日新增", "value": sum(int(item["created"]) for item in modules)},
        {"label": "待处理", "value": sum(int(item["pending"]) for item in modules)},
        {"label": "异常量", "value": sum(int(item["abnormal"]) for item in modules)},
    ]
    return {"cards": cards, "modules": modules}
