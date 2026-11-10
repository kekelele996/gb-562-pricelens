import type { TrendPoint } from '../../types/models';
import { fmtDateTime } from '../../utils/format';

interface Props {
  points: TrendPoint[];
}

export default function F1Trend({ points }: Props) {
  const width = 640;
  const height = 150;
  const padX = 34;
  const padY = 18;
  if (!points.length) {
    return <div className="banner">暂无批次数据</div>;
  }
  const xs = points.map((_, index) => padX + (index * (width - padX * 2)) / Math.max(points.length - 1, 1));
  const ys = points.map((point) => {
    const value = Math.max(0, Math.min(1, point.f1_score ?? 0));
    return padY + (1 - value) * (height - padY * 2);
  });
  const path = points.map((_, index) => `${index === 0 ? 'M' : 'L'}${xs[index].toFixed(1)},${ys[index].toFixed(1)}`).join(' ');
  const last = points[points.length - 1];
  return (
    <div>
      <svg className="trend" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="F1 趋势">
        {[0, 0.25, 0.5, 0.75, 1].map((value) => {
          const y = padY + (1 - value) * (height - padY * 2);
          return (
            <g key={value}>
              <line className="trend-grid" x1={padX} x2={width - padX} y1={y} y2={y} />
              <text className="trend-label" x={4} y={y + 3}>{value.toFixed(2)}</text>
            </g>
          );
        })}
        <path className="trend-line" d={path} />
        {points.map((point, index) => (
          <circle key={point.run_id} className="trend-dot" cx={xs[index]} cy={ys[index]} r={point.run_id === last.run_id ? 3.6 : 2.4}>
            <title>#{point.run_id} {point.site_name} v{point.version} F1 {point.f1_score?.toFixed(3)}</title>
          </circle>
        ))}
      </svg>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.66rem', color: 'var(--ink-soft)' }}>
        <span>{fmtDateTime(points[0].created_at)}</span>
        <span>
          最近：v{last.version} · F1 {last.f1_score?.toFixed(2) ?? '—'}
        </span>
        <span>{fmtDateTime(last.created_at)}</span>
      </div>
    </div>
  );
}
