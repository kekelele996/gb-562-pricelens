import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { templatesApi } from '../api/templates';
import { snapshotsApi } from '../api/snapshots';
import { useAsync } from '../hooks/useAsync';
import { uiStore } from '../stores/uiStore';
import StatusPill from '../components/common/StatusPill';
import { FIELD_STATUS_LABEL } from '../constants/enums';
import { errorMessage } from '../utils/errorMessage';
import { fmtDateTime } from '../utils/format';
import type { FieldRule, PreviewOut } from '../types/models';

export default function TemplateEditor() {
  const { id } = useParams();
  const templateId = Number(id);
  const navigate = useNavigate();
  const template = useAsync(() => templatesApi.get(templateId), [templateId]);
  const [rules, setRules] = useState<FieldRule[]>([]);
  const [preview, setPreview] = useState<PreviewOut | null>(null);
  const [previewError, setPreviewError] = useState('');
  const [saving, setSaving] = useState(false);
  const [snapshotId, setSnapshotId] = useState<number | null>(null);
  const snapshots = useAsync(() => snapshotsApi.list(template.data?.site_id), [template.data?.site_id]);

  useEffect(() => {
    if (template.data) {
      setRules(template.data.field_rules);
      templatesApi
        .preview(templateId)
        .then(setPreview)
        .catch(() => setPreviewError('预览加载失败'));
    }
  }, [template.data, templateId]);

  const hits = useMemo(() => preview?.fields.filter((field) => field.status === 'hit').length ?? 0, [preview]);

  async function saveRules() {
    setSaving(true);
    try {
      const updated = await templatesApi.update(templateId, rules, '编辑台手工微调候选选择器');
      setRules(updated.field_rules);
      uiStore.push('ok', `字段规则已保存，当前 v${updated.version}`);
    } catch (err) {
      uiStore.push('error', errorMessage((err as { payload?: unknown }).payload, '保存失败'));
    } finally {
      setSaving(false);
    }
  }

  async function runDiagnose() {
    const list = snapshots.data?.items ?? [];
    const latest = snapshotId ? list.find((item) => item.id === snapshotId) : list.find((item) => !item.is_baseline) ?? list[0];
    if (!latest) return;
    navigate(`/snapshots/${latest.id}/diagnose/${templateId}`);
  }

  if (template.error) {
    return <div className="banner error">模板加载失败，可能已被归档或不属于当前角色。</div>;
  }
  if (!template.data) {
    return <div className="main">正在打开模板编辑台 …</div>;
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <div className="kicker">Template / 编辑台</div>
          <h1>{template.data.name}</h1>
          <p className="sub">
            {template.data.site_name} · v{template.data.version} · 覆盖率 {(template.data.coverage_score * 100).toFixed(0)}% · 最近验证{' '}
            {fmtDateTime(template.data.last_verified_at)}
          </p>
        </div>
        <div className="head-actions">
          <StatusPill tone={template.data.status} label={template.data.status.toUpperCase()} />
          <button className="btn btn-ghost" onClick={saveRules} disabled={saving} data-testid="save-rules">
            {saving ? '保存中 …' : '保存字段规则'}
          </button>
          <button className="btn btn-primary" onClick={runDiagnose} data-testid="run-diagnose">
            查看快照诊断
          </button>
        </div>
      </div>

      {previewError ? <div className="banner error">{previewError}</div> : null}

      <div className="split">
        <div className="panel">
          <div className="panel-head">
            <h2>字段规则（{rules.length}）</h2>
            <span className="meta">
              候选命中 {hits}/{preview?.total ?? rules.length} · 快照 {preview?.snapshot_label ?? '—'}
            </span>
          </div>
          <div className="panel-body">
            <table className="data rule-table">
              <thead>
                <tr>
                  <th>字段</th>
                  <th>类型</th>
                  <th>首选候选选择器</th>
                  <th>后处理正则</th>
                  <th>已验证值</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((rule, index) => {
                  const result = preview?.fields.find((field) => field.field === rule.field);
                  return (
                    <tr key={rule.field} data-testid={`rule-${rule.field}`}>
                      <td>
                        {rule.label}
                        <div className="mono" style={{ color: 'var(--ink-faint)' }}>{rule.field}</div>
                      </td>
                      <td className="mono">{rule.type}</td>
                      <td>
                        <input
                          className="input"
                          style={{ padding: '0.25rem 0.4rem', fontSize: '0.74rem' }}
                          value={rule.selector_candidates[0] ?? ''}
                          onChange={(event) => {
                            const next = [...rules];
                            next[index] = { ...rule, selector_candidates: [event.target.value, ...rule.selector_candidates.slice(1)] };
                            setRules(next);
                          }}
                        />
                        <div style={{ fontSize: '0.62rem', color: 'var(--ink-faint)', marginTop: 2 }}>
                          备选 {rule.selector_candidates.length - 1} 条{rule.patched ? ' · 已自愈 patch' : ''}
                        </div>
                      </td>
                      <td className="mono">{rule.post_regex ?? '—'}</td>
                      <td className="mono">{rule.verified_value ?? '—'}</td>
                      <td>
                        {result ? <StatusPill tone={result.status} label={FIELD_STATUS_LABEL[result.status]} /> : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <h2>快照抽取预览</h2>
            <span className="meta">命中高亮</span>
          </div>
          <div className="panel-body">
            {(preview?.fields ?? []).map((field) => (
              <div key={field.field} style={{ marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <span style={{ fontSize: '0.7rem', letterSpacing: '0.08em', color: 'var(--ink-soft)' }}>{field.label}</span>
                  <span className="preview-value">{field.value ?? '—'}</span>
                </div>
                <div className="preview-snippet">
                  {field.value && field.snippet ? highlight(field.snippet, field.value) : '未命中该字段（选择器无匹配节点）'}
                </div>
              </div>
            ))}
            <div style={{ marginTop: '0.6rem', fontSize: '0.68rem', color: 'var(--ink-soft)' }}>
              高亮来自后端真实抽取结果，预览快照：
              <select
                className="input"
                style={{ width: 'auto', display: 'inline-block', marginLeft: 6, padding: '0.15rem 0.3rem', fontSize: '0.7rem' }}
                value={snapshotId ?? ''}
                onChange={(event) => {
                  const value = event.target.value ? Number(event.target.value) : null;
                  setSnapshotId(value);
                  templatesApi.preview(templateId, value ?? undefined).then(setPreview).catch(() => undefined);
                }}
              >
                <option value="">baseline</option>
                {(snapshots.data?.items ?? [])
                  .filter((item) => !item.is_baseline)
                  .map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.label}
                    </option>
                  ))}
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function highlight(snippet: string, value: string): React.ReactNode {
  const index = snippet.indexOf(value);
  if (index < 0) return snippet;
  return (
    <>
      {snippet.slice(0, index)}
      <mark>{value}</mark>
      {snippet.slice(index + value.length)}
    </>
  );
}
