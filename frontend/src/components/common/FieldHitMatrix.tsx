import type { FieldMatrixRow } from '../../types/models';
import { FIELD_STATUS_LABEL } from '../../constants/enums';
import StatusPill from './StatusPill';

interface Props {
  rows: FieldMatrixRow[];
  compact?: boolean;
}

export default function FieldHitMatrix({ rows, compact }: Props) {
  return (
    <div>
      <div className="matrix" style={{ marginBottom: compact ? 0 : '0.8rem' }}>
        <div className="matrix-row">
          <span className="cell-label">字段</span>
          <span className="cell-label">baseline</span>
          <span className="cell-label">新快照</span>
          <span className="cell-label">相似度</span>
        </div>
        {rows.map((row) => (
          <div className="matrix-row" key={row.field} data-testid={`matrix-${row.field}`}>
            <span className="cell-label">{row.label}</span>
            <span className={`matrix-cell ${row.baseline_status}`} title={row.baseline_value || '未抽到'} />
            <span className={`matrix-cell ${row.new_status}`} title={row.new_value || '未抽到'} />
            <span className="mono" style={{ fontSize: '0.68rem' }}>
              {(row.similarity ?? 0).toFixed(2)}
            </span>
          </div>
        ))}
      </div>
      {compact ? null : (
        <div className="matrix-legend">
          <span><i style={{ background: 'var(--copper)' }} />命中</span>
          <span><i style={{ background: 'var(--vermilion)' }} />错位</span>
          <span><i className="matrix-cell miss" style={{ width: 9, height: 9, display: 'inline-block' }} />缺失</span>
        </div>
      )}
      {rows.some((row) => row.new_status !== 'hit') ? (
        <div style={{ marginTop: '0.6rem', fontSize: '0.7rem', color: 'var(--ink-soft)' }}>
          异常字段：
          {rows
            .filter((row) => row.new_status !== 'hit')
            .map((row) => (
              <StatusPill
                key={row.field}
                tone={row.new_status}
                label={`${row.label}·${FIELD_STATUS_LABEL[row.new_status] ?? row.new_status}`}
              />
            ))}
        </div>
      ) : null}
    </div>
  );
}
