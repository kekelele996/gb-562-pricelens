"""审计日志动作模板（action 字段枚举来源）。"""
from __future__ import annotations

ACTIONS: dict[str, str] = {
    "auth.login": "登录",
    "site.create": "新增站点",
    "site.update": "修改站点",
    "template.create": "新增模板",
    "template.update": "更新字段规则",
    "template.apply_patch": "应用自愈候选生成新版本",
    "run.execute": "执行抽取批次",
    "diagnose.run": "触发漂移诊断",
    "alert.accepted": "接受告警",
    "alert.dismissed": "驳回告警",
    "report.export": "导出客户日报",
}
