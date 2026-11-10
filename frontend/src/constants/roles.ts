/** 角色 -> 权限点（README 与后端 src/constants/roles.py 一致）。 */
import type { Role } from '../types/models';

export const ROLE_LABEL: Record<Role, string> = {
  admin: '运营主管',
  analyst: '采集工程师',
  client: '品牌客户（只读）',
};

export const PERMISSIONS: Record<Role, string[]> = {
  admin: ['site:write', 'template:write', 'run:execute', 'diagnose:run', 'candidate:apply', 'alert:handle', 'report:read', 'audit:read'],
  analyst: ['template:write', 'run:execute', 'diagnose:run', 'candidate:apply', 'report:read', 'audit:read'],
  client: ['report:read'],
};

export function can(role: Role | undefined, permission: string): boolean {
  if (!role) return false;
  return PERMISSIONS[role]?.includes(permission) ?? false;
}
