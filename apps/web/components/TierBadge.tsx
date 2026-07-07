import type { Tier } from "@/lib/types";

// Ordinal ramp, best -> worst — one hue, darker means stronger, matching the
// dashboard's tier bar chart so the same tier always reads as the same color.
export const TIER_COLORS: Record<Tier, string> = {
  Serious: "var(--viz-ordinal-1)",
  Quality: "var(--viz-ordinal-2)",
  Interested: "var(--viz-ordinal-3)",
  "Not Qualified": "var(--viz-ordinal-4)",
};

export function TierBadge({ tier }: { tier: Tier }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--viz-border)] px-2 py-0.5 text-xs font-medium text-[var(--viz-text-primary)]">
      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: TIER_COLORS[tier] }} aria-hidden />
      {tier}
    </span>
  );
}
