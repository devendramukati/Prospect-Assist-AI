"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { TierBadge } from "@/components/TierBadge";
import type { LeadSummary, Tier } from "@/lib/types";

const TIER_OPTIONS: (Tier | "All")[] = ["All", "Serious", "Quality", "Interested", "Not Qualified"];

const CAPPED_BY_LABEL: Record<string, string> = {
  intent_gate: "Never started an application",
  discipline_gate: "Discipline red flag",
};

export function LeadsTable({ leads }: { leads: LeadSummary[] }) {
  const [tierFilter, setTierFilter] = useState<Tier | "All">("All");

  const filtered = useMemo(() => {
    const rows = tierFilter === "All" ? leads : leads.filter((lead) => lead.tier === tierFilter);
    return [...rows].sort((a, b) => b.composite_score - a.composite_score);
  }, [leads, tierFilter]);

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2">
        {TIER_OPTIONS.map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => setTierFilter(option)}
            className="rounded-full border px-3 py-1 text-xs font-medium transition-colors"
            style={{
              borderColor: "var(--viz-border)",
              backgroundColor: tierFilter === option ? "var(--viz-series-1)" : "transparent",
              color: tierFilter === option ? "#ffffff" : "var(--viz-text-secondary)",
            }}
          >
            {option}
          </button>
        ))}
      </div>

      <div className="mt-4 overflow-x-auto rounded-lg border border-[var(--viz-border)]">
        <table className="w-full min-w-[640px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-[var(--viz-border)] bg-[var(--viz-page-plane)] text-left text-xs uppercase tracking-wide text-[var(--viz-text-muted)]">
              <th className="px-4 py-2 font-medium">Customer</th>
              <th className="px-4 py-2 font-medium">Employment</th>
              <th className="px-4 py-2 font-medium">Tier</th>
              <th className="px-4 py-2 font-medium text-right">Score</th>
              <th className="px-4 py-2 font-medium">Capped by</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((lead) => (
              <tr key={lead.external_ref} className="border-b border-[var(--viz-border)] last:border-0">
                <td className="px-4 py-2">
                  <Link href={`/leads/${encodeURIComponent(lead.external_ref)}`} className="underline">
                    {lead.external_ref}
                  </Link>
                </td>
                <td className="px-4 py-2 text-[var(--viz-text-secondary)]">{lead.employment_type}</td>
                <td className="px-4 py-2">
                  <TierBadge tier={lead.tier} />
                </td>
                <td className="px-4 py-2 text-right [font-variant-numeric:tabular-nums]">
                  {lead.composite_score.toFixed(2)}
                </td>
                <td className="px-4 py-2 text-xs text-[var(--viz-text-muted)]">
                  {lead.capped_by ? CAPPED_BY_LABEL[lead.capped_by] : "—"}
                </td>
              </tr>
            ))}
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-[var(--viz-text-muted)]">
                  No leads in this tier.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
