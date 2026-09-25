"""模块台账：全部业务模块的展示口径只在这里定义一次。

概览统计、各模块列表、示例数据生成都以本模块为唯一口径来源，避免出现
“概览数一个值、点进列表又是另一个值”的情况：

- ``statuses`` 的最后一个状态是该模块的唯一办结状态，除此之外的记录一律算待处理；
- ``abnormal_statuses`` 列出算异常的状态（多为停用、作废、故障、不合格等）；
- ``pending`` / ``abnormal`` 两个布尔标记不再作为独立口径存储，统一由状态推导。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StatSpec:
    """模块页顶部统计卡片：label 与前端既有卡片保持一致。"""

    label: str
    rule: str  # total / pending / abnormal / terminal / status:<状态> / first


@dataclass(frozen=True)
class ModuleSpec:
    """单个业务模块的固定口径。"""

    key: str
    label: str
    entity: str
    code_prefix: str
    fields: tuple[str, ...]
    required_fields: tuple[str, ...]
    statuses: tuple[str, ...]
    action_rules: dict[str, str]
    abnormal_statuses: frozenset[str]
    stats: tuple[StatSpec, ...]
    keyword_field: str

    @property
    def terminal_status(self) -> str:
        """末态：进入该状态后不再算待处理。"""
        return self.statuses[-1]

    def is_pending(self, status: str | None) -> bool:
        """待处理口径：除末态以外的所有状态。"""
        return status != self.terminal_status

    def is_abnormal(self, status: str | None) -> bool:
        """异常口径：命中异常状态集合才算异常。"""
        return status in self.abnormal_statuses

    def decorate(self, row: dict) -> dict:
        """按状态补齐 pending/abnormal 两个派生标记。"""
        row["pending"] = self.is_pending(row.get("status"))
        row["abnormal"] = self.is_abnormal(row.get("status"))
        return row

    def stat_value(self, rule: str, rows: list[dict]) -> int:
        """按同一份列表数据计算单张统计卡片的数值。"""
        if rule == "total":
            return len(rows)
        if rule == "pending":
            return sum(1 for row in rows if self.is_pending(row.get("status")))
        if rule == "abnormal":
            return sum(1 for row in rows if self.is_abnormal(row.get("status")))
        if rule == "terminal":
            return sum(1 for row in rows if row.get("status") == self.terminal_status)
        if rule == "first":
            return sum(1 for row in rows if row.get("status") == self.statuses[0])
        if rule.startswith("status:"):
            target = rule.split(":", 1)[1]
            return sum(1 for row in rows if row.get("status") == target)
        raise ValueError(f"未知统计口径：{rule}")


def _stats(*pairs: tuple[str, str]) -> tuple[StatSpec, ...]:
    return tuple(StatSpec(label=label, rule=rule) for label, rule in pairs)


MODULES: tuple[ModuleSpec, ...] = (
    ModuleSpec(
        key="section",
        label="线路区段",
        entity="线路区段",
        code_prefix="SECT",
        fields=("区段编码", "区段名称", "所属线路", "起止里程", "管辖工区", "投运日期", "限速值", "区段状态"),
        required_fields=("区段编码", "区段名称", "所属线路"),
        statuses=("在建", "已投用", "限速运行", "已封闭"),
        action_rules={"办理投用": "已投用", "申请限速": "限速运行", "封闭区段": "已封闭"},
        abnormal_statuses=frozenset({"限速运行"}),
        stats=_stats(("在用区段", "status:已投用"), ("限速区段", "abnormal"), ("封闭区段", "terminal")),
        keyword_field="区段编码",
    ),
    ModuleSpec(
        key="signal",
        label="信号机",
        entity="信号机",
        code_prefix="SIGN",
        fields=("设备编号", "设备类型", "安装位置", "显示制式", "所属区段", "上次检修日", "下次检修日", "设备状态"),
        required_fields=("设备编号", "设备类型", "安装位置"),
        statuses=("待检修", "运用正常", "故障停用", "已更换"),
        action_rules={"确认检修": "运用正常", "登记故障": "故障停用", "更换设备": "已更换"},
        abnormal_statuses=frozenset({"故障停用"}),
        stats=_stats(("在运信号机", "status:运用正常"), ("待检修信号机", "first"), ("故障停用台数", "abnormal")),
        keyword_field="设备编号",
    ),
    ModuleSpec(
        key="switch",
        label="转辙机",
        entity="转辙机",
        code_prefix="SWIT",
        fields=("设备编号", "设备型号", "安装道岔", "动作电流", "转换时间", "所属区段", "上次检修日", "设备状态"),
        required_fields=("设备编号", "设备型号", "安装道岔"),
        statuses=("待检修", "运用正常", "动作异常", "已更换"),
        action_rules={"确认检修": "运用正常", "登记动作异常": "动作异常", "更换设备": "已更换"},
        abnormal_statuses=frozenset({"动作异常"}),
        stats=_stats(("在运转辙机", "status:运用正常"), ("动作异常台数", "abnormal"), ("待检修台数", "first")),
        keyword_field="设备编号",
    ),
    ModuleSpec(
        key="track",
        label="轨道电路",
        entity="轨道电路",
        code_prefix="TRAC",
        fields=("设备编号", "制式类型", "区段长度", "分路灵敏度", "所属区段", "上次测试日", "下次测试日", "设备状态"),
        required_fields=("设备编号", "制式类型", "区段长度"),
        statuses=("待测试", "运用正常", "分路不良", "已更换"),
        action_rules={"提交测试": "运用正常", "确认正常": "分路不良", "更换设备": "已更换"},
        abnormal_statuses=frozenset({"分路不良"}),
        stats=_stats(("在运轨道电路", "status:运用正常"), ("分路不良区段", "abnormal"), ("待测试设备", "first")),
        keyword_field="设备编号",
    ),
    ModuleSpec(
        key="interlock",
        label="联锁设备",
        entity="联锁设备",
        code_prefix="INTE",
        fields=("设备编号", "联锁类型", "控制范围", "软件版本", "所属车站", "上次检修日", "责任人", "设备状态"),
        required_fields=("设备编号", "联锁类型", "控制范围"),
        statuses=("待检修", "运用正常", "降级使用", "已停用"),
        action_rules={"确认检修": "运用正常", "降级登记": "降级使用", "停用设备": "已停用"},
        abnormal_statuses=frozenset({"降级使用", "已停用"}),
        stats=_stats(("在运联锁", "status:运用正常"), ("降级使用设备", "status:降级使用"), ("待检修设备", "first")),
        keyword_field="设备编号",
    ),
    ModuleSpec(
        key="atp",
        label="列车防护",
        entity="防护设备",
        code_prefix="ATP",
        fields=("设备编号", "防护等级", "覆盖区段", "应答器数量", "所属线路", "版本号", "责任人", "防护状态"),
        required_fields=("设备编号", "防护等级", "覆盖区段"),
        statuses=("待启用", "防护正常", "版本待升级", "已停用"),
        action_rules={"启用防护": "防护正常", "提交升级": "版本待升级", "停用防护": "已停用"},
        abnormal_statuses=frozenset({"版本待升级", "已停用"}),
        stats=_stats(("在运防护设备", "status:防护正常"), ("待升级版本", "status:版本待升级"), ("覆盖区段数", "total")),
        keyword_field="设备编号",
    ),
    ModuleSpec(
        key="plan",
        label="检修计划",
        entity="检修计划",
        code_prefix="PLAN",
        fields=("计划编号", "检修类型", "检修对象", "计划日期", "检修周期", "作业班组", "计划工时", "计划状态"),
        required_fields=("计划编号", "检修类型", "检修对象"),
        statuses=("待审批", "已批复", "执行中", "已作废"),
        action_rules={"提交审批": "已批复", "确认执行": "执行中", "作废计划": "已作废"},
        abnormal_statuses=frozenset({"已作废"}),
        stats=_stats(("待审批计划", "first"), ("执行中计划", "status:执行中"), ("本月计划数", "total")),
        keyword_field="计划编号",
    ),
    ModuleSpec(
        key="task",
        label="检修任务",
        entity="检修任务",
        code_prefix="TASK",
        fields=("任务编号", "关联计划", "检修人员", "开始时间", "完成时间", "检修项目数", "遗留问题数", "任务状态"),
        required_fields=("任务编号", "关联计划", "检修人员"),
        statuses=("待开始", "检修中", "待验收", "已完成"),
        action_rules={"开始任务": "检修中", "提交验收": "待验收", "确认完成": "已完成"},
        abnormal_statuses=frozenset(),
        stats=_stats(("待开始任务", "first"), ("检修中任务", "status:检修中"), ("遗留问题数", "pending")),
        keyword_field="任务编号",
    ),
    ModuleSpec(
        key="fault",
        label="故障登记",
        entity="设备故障",
        code_prefix="FAUL",
        fields=("故障编号", "发生设备", "故障现象", "影响范围", "发生时间", "报告人", "恢复时间", "故障状态"),
        required_fields=("故障编号", "发生设备", "故障现象"),
        statuses=("待定级", "已定级", "处置中", "已恢复", "已挂起"),
        action_rules={"确认定级": "已定级", "提交恢复": "已恢复", "挂起故障": "已挂起"},
        abnormal_statuses=frozenset({"处置中", "已挂起"}),
        stats=_stats(("待定级故障", "first"), ("处置中故障", "status:处置中"), ("今日恢复数", "terminal")),
        keyword_field="故障编号",
    ),
    ModuleSpec(
        key="dispose",
        label="故障处置",
        entity="处置单",
        code_prefix="DISP",
        fields=("处置单号", "关联故障", "处置措施", "更换器材", "处置人员", "完成时间", "验收人员", "处置状态"),
        required_fields=("处置单号", "关联故障", "处置措施"),
        statuses=("待受理", "处置中", "待验收", "已验收"),
        action_rules={"受理处置": "处置中", "提交验收": "待验收", "确认验收": "已验收"},
        abnormal_statuses=frozenset(),
        stats=_stats(("待受理处置", "first"), ("处置中单据", "status:处置中"), ("本月验收单数", "terminal")),
        keyword_field="处置单号",
    ),
    ModuleSpec(
        key="spare",
        label="器材领用",
        entity="器材领用单",
        code_prefix="SPAR",
        fields=("领用单号", "器材名称", "器材规格", "领用数量", "领用人员", "领用日期", "所属工区", "领用状态"),
        required_fields=("领用单号", "器材名称", "器材规格"),
        statuses=("待审批", "已批准", "已领用", "已退回"),
        action_rules={"批准领用": "已批准", "确认发放": "已领用", "退回器材": "已退回"},
        abnormal_statuses=frozenset({"已退回"}),
        stats=_stats(("待审批领用", "first"), ("本月领用单", "total"), ("退回单数", "abnormal")),
        keyword_field="领用单号",
    ),
    ModuleSpec(
        key="measure",
        label="电气测试",
        entity="测试单",
        code_prefix="MEAS",
        fields=("测试单号", "测试项目", "测试设备", "测试值", "标准范围", "测试结论", "测试人员", "测试状态"),
        required_fields=("测试单号", "测试项目", "测试设备"),
        statuses=("待测试", "测试中", "合格", "不合格"),
        action_rules={"开始测试": "测试中", "判定合格": "合格", "判定不合格": "不合格"},
        abnormal_statuses=frozenset({"不合格"}),
        stats=_stats(("待测试单据", "first"), ("测试合格率", "status:合格"), ("不合格项数", "abnormal")),
        keyword_field="测试单号",
    ),
    ModuleSpec(
        key="patrol",
        label="巡视检查",
        entity="巡视单",
        code_prefix="PATR",
        fields=("巡视单号", "巡视路线", "巡视人员", "巡视日期", "发现问题数", "整改项数", "巡视时长", "巡视状态"),
        required_fields=("巡视单号", "巡视路线", "巡视人员"),
        statuses=("待派发", "巡视中", "已提交", "已作废"),
        action_rules={"派发巡视": "巡视中", "提交结果": "已提交", "作废巡视": "已作废"},
        abnormal_statuses=frozenset({"已作废"}),
        stats=_stats(("待派发巡视", "first"), ("巡视中任务", "status:巡视中"), ("本月发现问题", "total")),
        keyword_field="巡视单号",
    ),
    ModuleSpec(
        key="window",
        label="天窗作业",
        entity="天窗计划",
        code_prefix="WIND",
        fields=("天窗编号", "作业类型", "作业区段", "计划时段", "实际时段", "申请单位", "负责人", "天窗状态"),
        required_fields=("天窗编号", "作业类型", "作业区段"),
        statuses=("待申请", "已批复", "作业中", "已销记"),
        action_rules={"提交申请": "已批复", "开始作业": "作业中", "销记天窗": "已销记"},
        abnormal_statuses=frozenset(),
        stats=_stats(("待申请天窗", "first"), ("作业中天窗", "status:作业中"), ("本月天窗数", "total")),
        keyword_field="天窗编号",
    ),
    ModuleSpec(
        key="alarm",
        label="监测报警",
        entity="报警事件",
        code_prefix="ALAR",
        fields=("报警编号", "报警类型", "报警等级", "触发设备", "触发时间", "确认人员", "处置说明", "报警状态"),
        required_fields=("报警编号", "报警类型", "报警等级"),
        statuses=("待确认", "已确认", "已处置", "已忽略"),
        action_rules={"确认报警": "已确认", "处置报警": "已处置", "忽略报警": "已忽略"},
        abnormal_statuses=frozenset({"已忽略"}),
        stats=_stats(("今日报警", "total"), ("待确认报警", "first"), ("高等级报警", "pending")),
        keyword_field="报警编号",
    ),
    ModuleSpec(
        key="verify",
        label="验收确认",
        entity="验收单",
        code_prefix="VERI",
        fields=("验收单号", "关联任务", "验收项目", "验收标准", "验收结论", "验收人员", "验收日期", "验收状态"),
        required_fields=("验收单号", "关联任务", "验收项目"),
        statuses=("待验收", "验收中", "已通过", "需返工"),
        action_rules={"开始验收": "验收中", "确认通过": "已通过", "下发返工": "需返工"},
        abnormal_statuses=frozenset({"需返工"}),
        stats=_stats(("待验收单据", "first"), ("本月通过数", "status:已通过"), ("需返工项数", "abnormal")),
        keyword_field="验收单号",
    ),
    ModuleSpec(
        key="shift",
        label="值班交接",
        entity="交接记录",
        code_prefix="SHIF",
        fields=("交接编号", "值班班组", "值班人员", "交接时间", "交接事项", "遗留事项", "接收人员", "交接状态"),
        required_fields=("交接编号", "值班班组", "值班人员"),
        statuses=("待交接", "交接中", "已交接", "已补录"),
        action_rules={"开始交接": "交接中", "确认接收": "已交接", "补录记录": "已补录"},
        abnormal_statuses=frozenset(),
        stats=_stats(("待交接记录", "first"), ("今日交接次数", "status:已交接"), ("遗留事项数", "pending")),
        keyword_field="交接编号",
    ),
    ModuleSpec(
        key="assess",
        label="状态评估",
        entity="评估记录",
        code_prefix="ASSE",
        fields=("评估编号", "评估对象", "评估周期", "健康分值", "风险等级", "评估人员", "评估结论", "评估状态"),
        required_fields=("评估编号", "评估对象", "评估周期"),
        statuses=("待评估", "评估中", "已定级", "已复评"),
        action_rules={"开始评估": "评估中", "确认定级": "已定级", "发起复评": "已复评"},
        abnormal_statuses=frozenset(),
        stats=_stats(("待评估对象", "first"), ("高风险设备", "pending"), ("健康分值均值", "total")),
        keyword_field="评估编号",
    ),
)

MODULE_SPECS: dict[str, ModuleSpec] = {spec.key: spec for spec in MODULES}
MODULE_ORDER: tuple[str, ...] = tuple(spec.key for spec in MODULES)
MODULE_LABELS: dict[str, str] = {spec.key: spec.label for spec in MODULES}


def get_spec(module: str) -> ModuleSpec:
    """读取模块口径；未知模块直接抛 KeyError，由上层转成可读错误。"""
    return MODULE_SPECS[module]
