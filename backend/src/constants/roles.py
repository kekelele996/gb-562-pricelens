"""角色 -> 权限点映射，README 与前端 constants/roles.ts 同步。"""
from __future__ import annotations

from src.constants.enums import Role

ROLE_LABELS: dict[str, str] = {
    Role.ADMIN.value: "运营主管",
    Role.ANALYST.value: "采集工程师",
    Role.CLIENT.value: "品牌客户（只读）",
}

PERMISSIONS: dict[str, set[str]] = {
    Role.ADMIN.value: {
        "site:write", "site:delete", "template:write", "template:delete",
        "run:execute", "diagnose:run", "candidate:apply", "alert:handle",
        "quota:write", "report:read", "audit:read",
    },
    Role.ANALYST.value: {
        "template:write", "run:execute", "diagnose:run",
        "candidate:apply", "report:read", "audit:read",
    },
    Role.CLIENT.value: {"report:read"},
}

# 写接口的角色白名单（controller 层 ROLE_GUARDS 使用）
SITE_WRITE_ROLES = (Role.ADMIN.value,)
TEMPLATE_WRITE_ROLES = (Role.ADMIN.value, Role.ANALYST.value)
RUN_EXECUTE_ROLES = (Role.ADMIN.value, Role.ANALYST.value)
ALERT_HANDLE_ROLES = (Role.ADMIN.value,)
REPORT_READ_ROLES = (Role.ADMIN.value, Role.ANALYST.value, Role.CLIENT.value)


def has_permission(role: str, permission: str) -> bool:
    return permission in PERMISSIONS.get(role, set())
