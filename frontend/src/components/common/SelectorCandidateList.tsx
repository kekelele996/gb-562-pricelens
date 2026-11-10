import type { HealField } from '../../types/models';
import { CANDIDATE_KIND_LABEL } from '../../constants/enums';
import StatusPill from './StatusPill';

interface Props {
  fields: HealField[];
  selected?: Record<string, string>;
  showActions?: boolean;
  onApplySingle?: (field: string, selector: string) => void;
}

export default function SelectorCandidateList({ fields, selected, showActions, onApplySingle }: Props) {
  const repairFields = fields.filter((field) => field.needs_repair);
  if (!repairFields.length) {
    return <div className="banner ok">全部字段命中，无需自愈。</div>;
  }
  return (
    <div>
      {repairFields.map((field) => (
        <div key={field.field} style={{ marginBottom: '1rem' }} data-testid={`candidates-${field.field}`}>
          <div className="candidate-head">
            <div>
              <strong style={{ fontFamily: 'var(--font-display)' }}>{field.label}</strong>
              <span className="mono" style={{ marginLeft: 8, color: 'var(--ink-soft)' }}>
                gt={field.verified_value ?? '—'}
              </span>
            </div>
            <StatusPill tone={field.current_status} label={`当前 ${field.current_status}`} />
          </div>
          <div className="candidate-meta">
            <span>历史批次 {field.history_runs} 次 · stability {field.stability.toFixed(2)}</span>
            <span>top1 置信 {field.confidence.toFixed(2)}</span>
            <span>
              {field.reason === 'no_candidate'
                ? '无可用候选（需人工映射）'
                : field.reason === 'low_confidence'
                  ? '候选置信不足，需人工确认'
                  : '达到自动应用阈值'}
            </span>
          </div>
          {field.candidates.map((candidate) => {
            const chosen = (selected?.[field.field] ?? field.selected) === candidate.selector;
            return (
              <div className={`candidate${chosen ? ' selected' : ''}`} key={`${field.field}-${candidate.selector}`}>
                <div className="candidate-head">
                  <span>
                    <span className="candidate-kind">{CANDIDATE_KIND_LABEL[candidate.kind] ?? candidate.kind}</span>
                    <code style={{ marginLeft: 8 }}>{candidate.selector}</code>
                  </span>
                  <span className="mono">{candidate.score.toFixed(4)}</span>
                </div>
                <div className="candidate-meta">
                  <span>抽取值 {candidate.value ?? '—'}</span>
                  <span>vsim {candidate.value_similarity.toFixed(3)}</span>
                  <span>stab {candidate.stability.toFixed(2)}</span>
                  <span>spec {candidate.specificity.toFixed(3)}</span>
                  <span>命中 {candidate.hit_count}</span>
                </div>
                {showActions && onApplySingle ? (
                  <button
                    className="btn btn-sm"
                    style={{ marginTop: '0.35rem' }}
                    disabled={!candidate.auto_applyable}
                    onClick={() => onApplySingle(field.field, candidate.selector)}
                  >
                    {candidate.auto_applyable ? '选用该候选' : '置信不足'}
                  </button>
                ) : null}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}
