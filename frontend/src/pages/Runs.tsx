import { useState } from 'react';
import { runsApi } from '../api/runs';
import { alertsApi } from '../api/alerts';
import { useAsync } from '../hooks/useAsync';
import F1Trend from '../components/common/F1Trend';
import FieldHitMatrix from '../components/common/FieldHitMatrix';
import StatusPill from '../components/common/StatusPill';
import { RUN_STATUS_LABEL, FIELD_STATUS_LABEL } from '../constants/enums';
import { fmtDateTime } from '../utils/format';
import type { Alert, Run } from '../types/models';

export default function Runs() {
  const { data, loading, error } = useAsync(() => runsApi.list(), []);
  const [selected, setSelected] = useState<Run | null>(null);
  const [alert, setAlert] = useState<Alert | null>(null);

  async function openRun(run: Run) {
    setSelected(run);
    setAlert(null);
    try {
      const alerts = await alertsApi.list();
      const matched = alerts.items.find((item) => item.snapshot_id === run.snapshot_id) ?? null;
      setAlert(matched);
    } catch {
      setAlert(null);
    }
  }

  if (error) return <div className="banner error">批次历史加载失败。</div>;
  if (loading && !data) return <div className="main">正在读取批次历史 …</div>;
  const runs = data?.items ?? [];
  const trend = data?.trend ?? [];

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="kicker">Runs / 抽取批次</div>
          <h1>批次历史与 F1 趋势</h1>
          <p className="sub">12 条种子批次 + 自愈重跑批次；F1 用 TP/FP/FN 口径真算并落库。</p>
        </div>
        <div className="head-actions">
          <StatusPill tone="active" label={`${runs.filter((run) => run.status === 'success').length} SUCCESS`} />
          <StatusPill tone="failed" label={`${runs.filter((run) => run.status === 'failed').length} FAILED`} />
        </div>
      </div>

      <div className="panel" style={{ marginBottom: '1.1rem' }}>
        <div className="panel-head">
          <h2>F1 趋势</h2>
          <span className="meta">最近 {trend.length} 条批次</span>
        </div>
        <div className="panel-body">
          <F1Trend points={trend} />
        </div>
      </div>

      <div className="split">
        <div className="panel">
          <div className="panel-head">
            <h2>批次列表</h2>
            <span className="meta">共 {data?.total ?? 0} 条</span>
          </div>
          <div className="panel-body" style={{ padding: 0 }}>
            <table className="data">
              <thead>
                <tr>
                  <th>#</th>
                  <th>站点</th>
                  <th>模板</th>
                  <th>状态</th>
                  <th>命中</th>
                  <th>F1</th>
                  <th>耗时</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.id} className="clickable" onClick={() => openRun(run)} data-testid={`run-row-${run.id}`}>
                    <td className="num">{run.id}</td>
                    <td>{run.site_name}</td>
                    <td className="mono">v{run.template_version}</td>
                    <td>
                      <StatusPill tone={run.status} label={RUN_STATUS_LABEL[run.status]} />
                    </td>
                    <td className="num">
                      {run.hit_fields}/{run.hit_fields + run.missing_fields}
                    </td>
                    <td className="num">{run.f1_score?.toFixed(2) ?? '—'}</td>
                    <td className="num">{run.duration_ms} ms</td>
                    <td className="mono">{fmtDateTime(run.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <h2>批次详情</h2>
            <span className="meta">{selected ? `#${selected.id}` : '选择左侧一行'}</span>
          </div>
          <div className="panel-body">
            {selected ? (
              <div>
                <dl className="kv" style={{ marginBottom: '0.8rem' }}>
                  <dt>站点 / 模板</dt>
                  <dd>
                    {selected.site_name} · {selected.template_name} v{selected.template_version}
                  </dd>
                  <dt>状态 / F1</dt>
                  <dd>
                    <StatusPill tone={selected.status} label={RUN_STATUS_LABEL[selected.status]} /> {selected.f1_score?.toFixed(4) ?? '—'}
                  </dd>
                  <dt>触发者</dt>
                  <dd className="mono">{selected.triggered_by}</dd>
                  <dt>错误信息</dt>
                  <dd>{selected.error_message ?? '—'}</dd>
                </dl>
                {alert ? (
                  <>
                    <p style={{ fontSize: '0.7rem', color: 'var(--ink-soft)', marginBottom: '0.5rem' }}>
                      关联告警 #{alert.id} · 漂移 {alert.drift_score.toFixed(2)}（{alert.severity}）
                    </p>
                    <FieldHitMatrix rows={alert.diagnosis.field_matrix} compact />
                  </>
                ) : (
                  <table className="data">
                    <thead>
                      <tr>
                        <th>字段</th>
                        <th>抽取值</th>
                        <th>状态</th>
                        <th>选择器</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selected.field_results.map((field) => (
                        <tr key={field.field}>
                          <td>{field.label}</td>
                          <td className="mono">{field.value ?? '—'}</td>
                          <td>
                            <StatusPill tone={field.status} label={FIELD_STATUS_LABEL[field.status]} />
                          </td>
                          <td className="mono wrap">{field.matched_selector ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            ) : (
              <p style={{ color: 'var(--ink-soft)', fontSize: '0.8rem' }}>
                点击批次行查看字段矩阵。F1 低于 0.6 的批次通常意味着站点改版导致模板静默错位。
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
