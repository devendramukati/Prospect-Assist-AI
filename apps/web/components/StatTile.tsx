interface StatTileProps {
  label: string;
  value: string;
  sublabel?: string;
}

export function StatTile({ label, value, sublabel }: StatTileProps) {
  return (
    <div className="rounded-lg border border-[var(--viz-border)] bg-[var(--viz-surface-1)] p-4">
      <p className="text-sm text-[var(--viz-text-muted)]">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-[var(--viz-text-primary)]">{value}</p>
      {sublabel ? <p className="mt-1 text-xs text-[var(--viz-text-secondary)]">{sublabel}</p> : null}
    </div>
  );
}
