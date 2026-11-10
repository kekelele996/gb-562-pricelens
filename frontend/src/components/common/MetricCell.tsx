interface Props {
  label: string;
  value: string | number;
  unit?: string;
  accent?: boolean;
}

export default function MetricCell({ label, value, unit, accent }: Props) {
  return (
    <div className="metric">
      <div className="k">{label}</div>
      <div className={`v${accent ? ' accent' : ''}`}>
        {value}
        {unit ? <small> {unit}</small> : null}
      </div>
    </div>
  );
}
