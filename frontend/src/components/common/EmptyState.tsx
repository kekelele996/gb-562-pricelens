interface Props {
  title: string;
  hint: string;
  action?: React.ReactNode;
}

export default function EmptyState({ title, hint, action }: Props) {
  return (
    <div className="empty">
      <strong>{title}</strong>
      <p>{hint}</p>
      {action ? <div style={{ marginTop: '0.8rem' }}>{action}</div> : null}
    </div>
  );
}
