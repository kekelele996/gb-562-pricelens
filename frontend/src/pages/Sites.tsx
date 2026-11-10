import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { sitesApi } from '../api/sites';
import { snapshotsApi } from '../api/snapshots';
import { useAsync } from '../hooks/useAsync';
import EmptyState from '../components/common/EmptyState';
import MetricCell from '../components/common/MetricCell';
import StatusPill from '../components/common/StatusPill';
import { fmtBytes, fmtDateTime } from '../utils/format';
import { TEMPLATE_STATUS_LABEL } from '../constants/enums';
import type { Snapshot } from '../types/models';

export default function Sites() {
  const navigate = useNavigate();
  const { data, loading, error } = useAsync(() => sitesApi.list(), []);
  const overview = useAsync(() => sitesApi.overview(), []);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [busy, setBusy] = useState(false);

  const sites = data?.items ?? [];
  const active = sites.find((site) => site.id === activeId) ?? sites[0];

  async function openDiagnose(siteId: number, templateId: number) {
    setBusy(true);
    try {
      const list = await snapshotsApi.list(siteId);
      const latest = list.items.find((item) => !item.is_baseline) ?? list.items[0];
      setSnapshots(list.items);
      if (latest) navigate(`/snapshots/${latest.id}/diagnose/${templateId}`);
    } finally {
      setBusy(false);
    }
  }

  if (error) {
    return <div className="banner error">站点列表加载失败，请刷新重试。</div>;
  }
  if (loading && !data) {
    return <div className="main">正在读取站点网格 …</div>;
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="kicker">Grid / 站点与模板</div>
          <h1>站点与抽取模板总览</h1>
          <p className="sub">6 个电商站点的模板版本、最近验证与告警分布；左侧竖排是采集网格。</p>
        </div>
        <div className="head-actions">
          {busy ? <StatusPill tone="draft" label="读取快照" /> : null}
          <span className="mono" style={{ fontSize: '0.7rem', color: 'var(--ink-soft)' }}>
            共 {sites.length} 站 · {overview.data?.active_templates ?? 0} 套生效模板
          </span>
        </div>
      </div>

      <div className="metrics">
        <MetricCell label="站点网格" value={overview.data?.sites ?? '—'} unit={`/ ${overview.data?.active_sites ?? 0} 活跃`} />
        <MetricCell label="模板版本" value={overview.data?.templates ?? '—'} unit={`/ ${overview.data?.active_templates ?? 0} 生效`} />
        <MetricCell label="待处置告警" value={overview.data?.open_alerts ?? 0} unit="条" accent />
        <MetricCell
          label="高危 / 关注"
          value={`${overview.data?.severity_counts?.high ?? 0} / ${overview.data?.severity_counts?.medium ?? 0}`}
          unit="条"
        />
      </div>

      <div className="split-narrow">
        <div className="site-rail">
          {sites.map((site) => (
            <button
              key={site.id}
              className={`site-rail-item${active?.id === site.id ? ' active' : ''}`}
              onClick={() => setActiveId(site.id)}
              data-testid={`site-rail-${site.id}`}
            >
              <strong>
                {site.name}
                {site.alert_count > 0 ? <span className="badge-dot" title={`${site.alert_count} 条待处置告警`} /> : null}
              </strong>
              <span>
                {site.domain} · {site.market} · QPS {site.qps_limit}
              </span>
            </button>
          ))}
        </div>
        <div>
          {active ? (
            <div>
              <div className="panel-head" style={{ borderBottom: '1px solid var(--line-strong)' }}>
                <div>
                  <h2>{active.name}</h2>
                  <div className="meta">
                    {active.domain} · robots {active.robots_policy} · {active.status === 'active' ? '采集中' : '已暂停'} · 最近抓取{' '}
                    {fmtDateTime(active.last_crawled_at)}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <StatusPill tone={active.status === 'active' ? 'active' : 'draft'} label={active.status === 'active' ? 'ACTIVE' : 'PAUSED'} />
                  {active.alert_count > 0 ? <StatusPill tone="high" label={`${active.alert_count} ALERT`} /> : null}
                </div>
              </div>
              <div className="panel-body">
                <table className="data rule-table">
                  <thead>
                    <tr>
                      <th>模板</th>
                      <th>版本</th>
                      <th>状态</th>
                      <th>字段</th>
                      <th>覆盖率</th>
                      <th>最近验证</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {active.templates.map((template) => (
                      <tr key={template.id}>
                        <td>{template.name}</td>
                        <td className="num">v{template.version}</td>
                        <td>
                          <StatusPill tone={template.status} label={TEMPLATE_STATUS_LABEL[template.status] ?? template.status} />
                        </td>
                        <td className="num">{template.field_count}</td>
                        <td className="num">{(template.coverage_score * 100).toFixed(0)}%</td>
                        <td className="mono">—</td>
                        <td>
                          <button
                            className="btn btn-sm"
                            data-testid={`open-template-${template.id}`}
                            onClick={() => {
                              if (template.status === 'deprecated') return;
                              navigate(`/templates/${template.id}`);
                            }}
                            disabled={template.status === 'deprecated'}
                          >
                            打开编辑台
                          </button>{' '}
                          <button
                            className="btn btn-sm btn-ghost"
                            data-testid={`diagnose-${template.id}`}
                            onClick={() => openDiagnose(active.id, template.id)}
                            disabled={template.status !== 'active'}
                          >
                            快照诊断
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {snapshots.length ? (
                  <p style={{ marginTop: '0.8rem', fontSize: '0.7rem', color: 'var(--ink-soft)' }}>
                    最近快照：{snapshots.slice(0, 2).map((item) => `${item.label}（${fmtBytes(item.byte_size)}）`).join(' · ')}
                  </p>
                ) : null}
              </div>
            </div>
          ) : (
            <EmptyState title="还没有站点" hint="先在数据库种子或 POST /api/sites 建立采集网格。" />
          )}
        </div>
      </div>
    </div>
  );
}
