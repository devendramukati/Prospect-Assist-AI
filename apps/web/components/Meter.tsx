type MeterStatus = "good" | "warning" | "serious" | "critical";

const STATUS_COLOR: Record<MeterStatus, string> = {
  good: "var(--viz-status-good)",
  warning: "var(--viz-status-warning)",
  serious: "var(--viz-status-serious)",
  critical: "var(--viz-status-critical)",
};

interface MeterProps {
  label: string;
  valuePct: number; // 0-100
  status: MeterStatus;
}

export function Meter({ label, valuePct, status }: MeterProps) {
  const clamped = Math.max(0, Math.min(100, valuePct));

  return (
    <div>
      <div className="flex items-baseline justify-between">
        <p className="text-sm text-[var(--viz-text-secondary)]">{label}</p>
        <p className="text-sm font-medium text-[var(--viz-text-primary)] [font-variant-numeric:tabular-nums]">
          {valuePct.toFixed(1)}%
        </p>
      </div>
      <div className="mt-1 h-2 w-full rounded-full" style={{ backgroundColor: "var(--viz-gridline)" }}>
        <div className="h-2 rounded-full" style={{ width: `${clamped}%`, backgroundColor: STATUS_COLOR[status] }} />
      </div>
    </div>
  );
}
