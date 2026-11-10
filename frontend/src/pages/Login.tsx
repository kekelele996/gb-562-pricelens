import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api/auth';
import { authStore } from '../stores/authStore';
import { errorMessage } from '../utils/errorMessage';

const DEMO_ACCOUNTS = [
  { email: 'admin@pricelens.io', label: '运营主管' },
  { email: 'analyst@pricelens.io', label: '采集工程师' },
  { email: 'client@pricelens.io', label: '品牌客户' },
];

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('analyst@pricelens.io');
  const [password, setPassword] = useState('Demo@2026');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      const result = await authApi.login(email, password);
      authStore.setSession(result.access_token, result.user);
      navigate(result.user.role === 'client' ? '/client/report' : '/sites', { replace: true });
    } catch (err) {
      setError(errorMessage((err as { payload?: unknown }).payload, '登录失败'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login">
      <section className="login-brand">
        <div>
          <div className="login-mark">
            pricelens<span>.</span>
          </div>
          <p className="login-tag">
            竞品价格采集与抽取模板自愈台 · 价眼数据（杭州，12 人）· 6 品牌 40 站点全网格价格日报
          </p>
        </div>
        <div>
          <p className="login-quote">
            站点改版不可怕，
            <br />
            可怕的是<em>第二天才发现</em>报表空了一列。
          </p>
          <div className="login-stats">
            <div className="login-stat">
              <strong>06:00</strong>
              <span>每日批次</span>
            </div>
            <div className="login-stat">
              <strong>0.42</strong>
              <span>昨夜漂移评分</span>
            </div>
            <div className="login-stat">
              <strong>92%</strong>
              <span>自愈后 F1</span>
            </div>
          </div>
        </div>
      </section>
      <section className="login-panel">
        <form className="login-card" onSubmit={submit}>
          <h1>校准台登录</h1>
          <p className="sub">模板、快照与告警都在这块黑板前处理。</p>
          <label className="field">
            <span>邮箱</span>
            <input
              className="input"
              type="email"
              value={email}
              autoComplete="username"
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label className="field">
            <span>密码</span>
            <input
              className="input"
              type="password"
              value={password}
              autoComplete="current-password"
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          <button className="btn btn-primary" style={{ width: '100%' }} type="submit" disabled={busy}>
            {busy ? '校验中 …' : '进入校准台'}
          </button>
          {error ? <div className="form-error">{error}</div> : null}
          <div className="hint-accounts">
            演示账号（密码统一 Demo@2026）：
            {DEMO_ACCOUNTS.map((account) => (
              <button
                key={account.email}
                type="button"
                onClick={() => {
                  setEmail(account.email);
                  setPassword('Demo@2026');
                }}
              >
                {account.label}
              </button>
            ))}
          </div>
        </form>
      </section>
    </div>
  );
}
