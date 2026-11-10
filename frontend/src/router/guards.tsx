import { Navigate, useLocation } from 'react-router-dom';
import { useSyncExternalStore } from 'react';
import { authStore } from '../stores/authStore';
import { can } from '../constants/roles';
import type { Role } from '../types/models';

export function useAuth() {
  return useSyncExternalStore(authStore.subscribe, authStore.getState);
}

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const state = useAuth();
  const location = useLocation();
  if (!state.bootstrapped) {
    return <div className="main" style={{ padding: 40 }}>正在恢复登录态 …</div>;
  }
  if (!state.token) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <>{children}</>;
}

export function RequirePermission({ permission, children }: { permission: string; children: React.ReactNode }) {
  const state = useAuth();
  if (!state.user || !can(state.user.role, permission)) {
    return (
      <div className="forbidden" data-testid="forbidden">
        <div>
          <div style={{ letterSpacing: '0.3em', fontSize: '0.7rem', color: 'var(--ink-soft)' }}>403 · FORBIDDEN</div>
          <h1>这页不在你的权限范围</h1>
          <p style={{ color: 'var(--ink-soft)', maxWidth: 420 }}>
            当前角色 {state.user ? ROLE_LABELS[state.user.role as Role] : '访客'} 只能查看客户日报与导出 CSV；
            模板、诊断和告警操作需要采集工程师或运营主管权限。
          </p>
        </div>
      </div>
    );
  }
  return <>{children}</>;
}

const ROLE_LABELS: Record<Role, string> = {
  admin: '运营主管',
  analyst: '采集工程师',
  client: '品牌客户（只读）',
};
