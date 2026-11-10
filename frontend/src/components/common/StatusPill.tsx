interface Props {
  tone: string;
  label: string;
  title?: string;
}

export default function StatusPill({ tone, label, title }: Props) {
  return (
    <span className={`pill tone-${tone}`} title={title}>
      {label}
    </span>
  );
}
