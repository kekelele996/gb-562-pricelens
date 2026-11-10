import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { alertsApi } from '../api/alerts';
import { snapshotsApi } from '../api/snapshots';
import { runsApi } from '../api/runs';
import { templatesApi } from '../api/templates';
import FieldHitMatrix from '../components/common/FieldHitMatrix';
import ScoreDial from '../components/common/ScoreDial';
import SelectorCandidateList from '../components/common/SelectorCandidateList';
import StatusPill from '../components/common/StatusPill';
import { uiStore } from '../stores/uiStore';
import { errorMessage } from '../utils/errorMessage';
import { fmtDateTime } from '../utils/format';
import { SEVERITY_LABEL } from '../constants/enums';
import type { Alert, Run, Snapshot, Template } from '../types/models';

export default function Diagnose() {
  const params = useParams();
  const navigate = useNavigate();
  const snapshotId = Number(params.snapshotId);
  const templateId = Number(params.templateId);
  const [alert, setAlert] = useState<Alert | null>(null);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [template, setTemplate] = useState<Template | null>(null);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [latestRun, setLatestRun] = useState<Run | null>(null);
  const [beforeRun, setBeforeRun] = useState<Run | null>(null);

  const load = useCallback(async () => {
    setError('');
    try {
      const [snapshotData, templateData] = await Promise.all([
        snapshotsApi.get(snapshotId),
        templatesApi.get(templateId),
      ]);
      setSnapshot(snapshotData);
      setTemplate(templateData);
      const alerts = await alertsApi.list();
      const matched = alerts.items.find((item) => item.snapshot_id === snapshotId && item.template_id === templateId);
      if (matched) {
        setAlert(matched);
      } else {
        const created = await snapshotsApi.diagnose(snapshotId, templateId);
        setAlert(created);
      }
      const runs = await runsApi.list(templateData.site_id);
      const forTemplate = runs.items.filter((run) => run.snapshot_id === snapshotId);
      setLatestRun(forTemplate[0] ?? null);
      setBeforeRun(forTemplate[1] ?? null);
    } catch (err) {
      setError(errorMessage((err as { payload?: unknown }).payload, '诊断加载失败'));
    }
  }, [snapshotId, templateId]);

  useEffect(() => {
    load();
  }, [load]);

  async function rerunDiagnose() {
    setBusy('diagnose');
    try {
      const updated = await snapshotsApi.diagnose(snapshotId, templateId);
      setAlert(updated);
      uiStore.push('ok', `漂移重算完成：${updated.drift_score.toFixed(2)} / ${updated.severity}`);
    } catch (err) {
      uiStore.push('error', errorMessage((err as { payload?: unknown }).payload, '诊断失败'));
    } finally {
      setBusy('');
    }
  }

  async function recompute() {
    if (!alert) return;
    setBusy('candidates');
    try {
      const result = await alertsApi.candidates(alert.id);
      setAlert(result.alert);
      uiStore.push('ok', `候选自愈评分完成，可自动应用 ${result.suggested_patch.auto_apply_count} 个字段`);
    } catch (err) {
      uiStore.push('error', errorMessage((err as { payload?: unknown }).payload, '候选生成失败'));
    } finally {
      setBusy('');
    }
  }

  async function apply() {
    if (!alert) return;
    setBusy('apply');
    try {
      const result = await alertsApi.apply(alert.id);
      uiStore.push('ok', `已生成 ${result.template.name} v${result.template.version}，并自动重跑批次`);
      navigate(`/templates/${result.template.id}`);
    } catch (err) {
      uiStore.push('error', errorMessage((err as { payload?: unknown }).payload, '应用候选失败'));
    } finally {
      setBusy('');
    }
  }

  if (error) return <div className="banner error">{error}</div>;
  if (!alert || !snapshot || !template) return <div className="main">正在读取快照与告警 …</div>;

  const diagnosis = alert.diagnosis;
  const patch = alert.suggested_patch;
  const matrix = diagnosis.field_matrix;

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="kicker">Diagnose / 快照诊断</div>
          <h1>{snapshot.site_name} · 快照 #{snapshot.id}</h1>
          <p className="sub">
            {snapshot.url} · {snapshot.label} · {fmtDateTime(snapshot.captured_at)} · 模板 {template.name} v{template.version}
          </p>
        </div>
        <div className="head-actions">
          <StatusPill tone={alert.severity} label={`${SEVERITY_LABEL[alert.severity]} ${alert.drift_score.toFixed(2)}`} />
          <button className="btn btn-ghost" onClick={rerunDiagnose} disabled={busy !== ''} data-testid="rerun-diagnose">
            {busy === 'diagnose' ? '重算中 …' : '重新诊断'}
          </button>
          <button className="btn" onClick={recompute} disabled={busy !== ''} data-testid="recompute-candidates">
            {busy === 'candidates' ? '评分中 …' : '重算候选'}
          </button>
          <button className="btn btn-primary" onClick={apply} disabled={busy !== '' || patch.auto_apply_count === 0} data-testid="apply-candidates">
            {busy === 'apply' ? '生成中 …' : `应用候选生成 v${template.version + 1}`}
          </button>
        </div>
      </div>

      <div className="metrics">
        {(() => null)()}
        <div className="metric">
          <div className="k">漂移评分</div>
          <div className="v accent">{alert.drift_score.toFixed(2)}</div>
        </div>
        <div className="metric">
          <div className="k">字段命中</div>
          <div className="v">
            {matrix.filter((row) => row.new_status !== 'hit').length}
            <small> / {matrix.length} 异常</small>
          </div>
        </div>
        <div className="metric">
          <div className="k">可自动应用</div>
          <div className="v">
            {patch.auto_apply_count}
            <small> 个字段</small>
          </div>
        </div>
        <div className="metric">
          <div className="k">自愈后批次 F1</div>
          <div className="v">
            {latestRun?.f1_score?.toFixed(2) ?? '待跑'}
            <small>{beforeRun?.f1_score ? `（前次 ${beforeRun.f1_score.toFixed(2)}）` : ''}</small>
          </div>
        </div>
      </div>

      <div className="split">
        <div>
          <div className="panel" style={{ marginBottom: '1.1rem' }}>
            <div className="panel-head">
              <h2>DOM 漂移诊断</h2>
              <span className="meta">算法 A · drift_detector.py</span>
            </div>
            <div className="panel-body">
              <ScoreDial score={alert.drift_score} severity={alert.severity} components={diagnosis.components} />
              <ul className="reason-list" style={{ marginTop: '0.9rem', paddingLeft: 0 }}>
                {(diagnosis.reason_codes ?? []).slice(0, 5).map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
              <div style={{ marginTop: '0.9rem', fontSize: '0.72rem', color: 'var(--ink-soft)' }}>
                变化子树 top{Math.min(3, diagnosis.top_changed_subtrees.length)}：
                {diagnosis.top_changed_subtrees.map((item) => (
                  <div key={item.path} className="mono" style={{ marginTop: 2 }}>
                    {item.path} <span style={{ color: 'var(--vermilion)' }}>+{item.added}</span> / <span style={{ color: 'var(--copper)' }}>-{item.removed}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head">
              <h2>逐字段命中矩阵</h2>
              <span className="meta">baseline → 新快照</span>
            </div>
            <div className="panel-body">
              <FieldHitMatrix rows={matrix} />
              {latestRun ? (
                <div style={{ marginTop: '0.8rem', borderTop: '1px dashed var(--line-strong)', paddingTop: '0.6rem', fontSize: '0.72rem' }}>
                  最近批次 #{latestRun.id}：F1 {latestRun.f1_score?.toFixed(2)} · 命中 {latestRun.hit_fields} · 模板 v{latestRun.template_version} ·{' '}
                  <a href={`/runs`}>查看批次历史</a>
                </div>
              ) : null}
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <h2>自愈候选评分</h2>
            <span className="meta">算法 B · 阈值 {patch.threshold}</span>
          </div>
          <div className="panel-body">
            <p style={{ fontSize: '0.7rem', color: 'var(--ink-soft)', marginBottom: '0.7rem' }}>
              score = 0.4·value_similarity + 0.3·stability + 0.2·specificity + 0.1·(1-hit_penalty)
            </p>
            <SelectorCandidateList fields={patch.fields} />
            <div className="banner" style={{ marginTop: '0.8rem' }}>
              应用后系统会把每个字段 top1 候选写入模板新版本（旧版本自动归档），并用新模板在同一快照上重跑一次批次。
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
