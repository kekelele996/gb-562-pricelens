import { useState } from 'react';
import { alertsApi } from '../api/alerts';
import { templatesApi } from '../api/templates';
import { useAsync } from '../hooks/useAsync';
import { useSyncExternalStore } from 'react';
import { authStore } from '../stores/authStore';
import { can } from '../constants/roles';
import SelectorCandidateList from '../components/common/SelectorCandidateList';
import StatusPill from '../components/common/StatusPill';
import { uiStore } from '../stores/uiStore';
import { ALERT_STATUS_LABEL, SEVERITY_LABEL } from '../constants/enums';
import { errorMessage } from '../utils/errorMessage';
import { fmtDateTime } from '../utils/format';
import type { Alert } from '../types/models';

export default function Alerts() {
  const { data, loading, error, reload } = useAsync(() => alertsApi.list(), []);
  const state = useSyncExternalStore(authStore.subscribe, authStore.getState);
  const [selected, setSelected] = useState<Alert | null>(null);
  const [busy, setBusy] = useState('');

  const alerts = data?.items ?? [];

  async function act(action: 'accept' | 'dismiss' | 'candidates' | 'apply', target: Alert) {
    setBusy(action);
    try {
      if (action === 'accept' || action === 'dismiss') {
        const result = await alertsApi.changeStatus(target.id, action === 'accept' ? 'accepted' : 'dismissed',
          action === 'accept' ? '人工确认：已核对页面改版，采纳告警' : '误报：页面 A/B 实验导致');
        uiStore.push('ok', `告警已${action === 'accept' ? '接受' : '驳回'}，审计日志 +${result.audit_added} 条`);
        reload();
      } else if (action === 'candidates') {
        const result = await alertsApi.candidates(target.id);
        setSelected(result.alert);
        uiStore.push('ok', '候选评分已重算');
      } else {
        const result = await alertsApi.apply(target.id);
        uiStore.push('ok', `已应用候选并生成 v${result.template.version}`);
        setSelected({ ...target, suggested_patch: { ...target.suggested_patch, patch: {} } });
        reload();
      }
    } catch (err) {
      uiStore.push('error', errorMessage((err as { payload?: unknown }).payload, '操作失败'));
    } finally {
      setBusy('');
    }
  }

  if (error) return <div className="banner error">告警队列加载失败。</div>;
  if (loading && !data) return <div className="main">正在读取告警队列 …</div>;

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="kicker">Alerts / 处置队列</div>
          <h1>漂移告警队列</h1>
          <p className="sub">诊断与候选均来自真实 HTML 快照计算；accepted / dismissed 写入审计日志。</p>
        </div>
        <div className="head-actions">
          <StatusPill tone="high" label={`${data?.open_count ?? 0} OPEN`} />
          <span className="mono" style={{ fontSize: '0.7rem', color: 'var(--ink-soft)' }}>
            共 {data?.total ?? 0} 条
          </span>
        </div>
      </div>

      <div className="split">
        <div className="panel">
          <div className="panel-head">
            <h2>告警列表</h2>
            <span className="meta">按漂移评分排序</span>
          </div>
          <div className="panel-body" style={{ padding: 0 }}>
            <table className="data">
              <thead>
                <tr>
                  <th>#</th>
                  <th>站点</th>
                  <th>评分</th>
                  <th>等级</th>
                  <th>状态</th>
                  <th>可应用</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert) => (
                  <tr key={alert.id} className="clickable" onClick={() => setSelected(alert)} data-testid={`alert-row-${alert.id}`}>
                    <td className="num">{alert.id}</td>
                    <td>{alert.site_name}</td>
                    <td className="num">{alert.drift_score.toFixed(2)}</td>
                    <td>
                      <StatusPill tone={alert.severity} label={SEVERITY_LABEL[alert.severity]} />
                    </td>
                    <td>
                      <StatusPill tone={alert.status} label={ALERT_STATUS_LABEL[alert.status]} />
                    </td>
                    <td className="num">{alert.suggested_patch?.auto_apply_count ?? 0}</td>
                    <td className="mono">{fmtDateTime(alert.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <h2>处置面板</h2>
            <span className="meta">{selected ? `#${selected.id}` : '选择左侧告警'}</span>
          </div>
          <div className="panel-body">
            {selected ? (
              <div>
                <div className="dial" style={{ marginBottom: '0.8rem' }}>
                  <div>
                    <div className="dial-num" style={{ fontSize: 'var(--step-3)' }}>{selected.drift_score.toFixed(2)}</div>
                    <div className="dial-caption">
                      {selected.site_name} · {SEVERITY_LABEL[selected.severity]} · {ALERT_STATUS_LABEL[selected.status]}
                    </div>
                  </div>
                </div>
                <SelectorCandidateList fields={selected.suggested_patch?.fields ?? []} />
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.8rem' }}>
                  <button className="btn" onClick={() => act('candidates', selected)} disabled={busy !== ''} data-testid="alert-recompute">
                    {busy === 'candidates' ? '评分中 …' : '重算候选'}
                  </button>
                  <button
                    className="btn btn-primary"
                    onClick={() => act('apply', selected)}
                    disabled={busy !== '' || !can(state.user?.role, 'candidate:apply')}
                    data-testid="alert-apply"
                  >
                    应用候选生成新版本
                  </button>
                  <button
                    className="btn"
                    onClick={() => {
                      templatesApi.get(selected.template_id ?? 0).then((template) => {
                        window.location.href = `/templates/${template.id}`;
                      });
                    }}
                  >
                    打开模板编辑台
                  </button>
                  {can(state.user?.role, 'alert:handle') ? (
                    <>
                      <button className="btn" onClick={() => act('accept', selected)} disabled={busy !== ''} data-testid="alert-accept">
                        接受告警
                      </button>
                      <button className="btn btn-ghost" onClick={() => act('dismiss', selected)} disabled={busy !== ''}>
                        驳回误报
                      </button>
                    </>
                  ) : null}
                </div>
                {selected.handled_by ? (
                  <p style={{ marginTop: '0.6rem', fontSize: '0.7rem', color: 'var(--ink-soft)' }}>
                    处置人 {selected.handled_by} · {selected.handle_note ?? '无备注'}
                  </p>
                ) : null}
              </div>
            ) : (
              <p style={{ color: 'var(--ink-soft)', fontSize: '0.8rem' }}>选择一条告警查看诊断摘要与自愈候选。</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
