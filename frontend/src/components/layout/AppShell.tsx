import { NavLink, useNavigate } from 'react-router-dom';
import { useSyncExternalStore } from 'react';
import { authStore } from '../../stores/authStore';
import { NAV_ITEMS } from '../../constants/ui';
import { ROLE_LABEL } from '../../constants/roles';
import Toasts from '../common/Toasts';

export default function AppShell({ children }: { children: React.ReactNode }) {
  const state = useSyncExternalStore(authStore.subscribe, authStore.getState);
  const navigate = useNavigate();
  const isClient = state.user?.role === 'client';
  const navItems = isClient ? NAV_ITEMS.filter((item) => item.to === '/client/report') : NAV_ITEMS;

  return (
    <div className="shell">
      <aside className="rail">
        <div className="rail-mark">
          pricelens
          <small>PRICE · WATCH</small>
        </div>
        <nav className="rail-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `rail-link${isActive ? ' active' : ''}`}
            >
              <span>{item.label}</span>
              <span className="k">{item.hint}</span>
            </NavLink>
          ))}
        </nav>
        <div className="rail-foot">
          <div className="rail-user">
            {state.user?.display_name ?? '未登录'}
            <small>{state.user ? ROLE_LABEL[state.user.role] : ''}</small>
          </div>
          <button
            className="link-btn"
            onClick={() => {
              authStore.logout();
              navigate('/login');
            }}
          >
            退出登录
          </button>
        </div>
      </aside>
      <main className="main">
        {state.user ? (
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.68rem', letterSpacing: '0.12em', color: 'var(--ink-faint)', textTransform: 'uppercase' }}>
              早市行情黑板 · 06:00 批次 · {state.user.email}
            </span>
          </div>
        ) : null}
        {children}
      </main>
      <Toasts />
    </div>
  );
}
