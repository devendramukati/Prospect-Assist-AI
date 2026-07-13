import Link from "next/link";

import { StatTile } from "@/components/StatTile";
import { getLeads } from "@/lib/api-client";
import type { Tier } from "@/lib/types";

import { ConversionComparisonChart } from "./components/ConversionComparisonChart";
import { DisciplineFlagRateChart } from "./components/DisciplineFlagRateChart";
import { TierBarChart } from "./components/TierBarChart";

const TIER_ORDER: Tier[] = ["Serious", "Quality", "Interested", "Not Qualified"];

function pct(n: number, d: number): number {
  return d > 0 ? n / d : 0;
}

export default async function DashboardPage() {
  const data = await getLeads();
  const leads = data?.leads ?? [];
  const total = leads.length;

  const tierCounts = TIER_ORDER.map((tier) => ({
    tier,
    count: leads.filter((lead) => lead.tier === tier).length,
  }));

  const targeted = leads.filter((lead) => lead.tier === "Serious" || lead.tier === "Quality");
  const baselineConversionRate = pct(leads.filter((lead) => lead.reached_disbursed).length, total);
  const targetedConversionRate = pct(
    targeted.filter((lead) => lead.reached_disbursed).length,
    targeted.length,
  );

  const disciplineFlagRateByTier = TIER_ORDER.map((tier) => {
    const tierLeads = leads.filter((lead) => lead.tier === tier);
    return {
      tier,
      ratePct: Math.round(pct(tierLeads.filter((lead) => lead.discipline_flagged).length, tierLeads.length) * 1000) / 10,
    };
  });

  const avgCompositeScore = total > 0 ? leads.reduce((sum, lead) => sum + lead.composite_score, 0) / total : 0;
  const disciplineFlaggedCount = leads.filter((lead) => lead.discipline_flagged).length;

  if (!data) {
    return (
      <main className="mx-auto max-w-5xl p-8">
        <h1 className="text-2xl font-semibold">Relationship Manager Dashboard</h1>
        <p className="mt-2 text-[var(--viz-status-critical)]">
          Could not reach the scoring service. Is it running and has synthetic data been generated?
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl p-8">
      <div className="flex items-baseline justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Relationship Manager Dashboard</h1>
          <p className="mt-1 text-sm text-[var(--viz-text-secondary)]">
            Portfolio overview across every scored prospect this period.
          </p>
        </div>
        <Link href="/leads" className="text-sm underline text-[var(--viz-text-secondary)]">
          View full lead list &rarr;
        </Link>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatTile label="Total leads" value={total.toLocaleString()} />
        <StatTile
          label="Serious + Quality"
          value={targeted.length.toLocaleString()}
          sublabel={`${Math.round(pct(targeted.length, total) * 100)}% of all leads`}
        />
        <StatTile label="Avg composite score" value={avgCompositeScore.toFixed(2)} />
        <StatTile
          label="Discipline red flags"
          value={disciplineFlaggedCount.toLocaleString()}
          sublabel="bounced payment or high day-1 spend velocity"
        />
      </div>

      <section className="mt-8 rounded-lg border border-[var(--viz-border)] bg-[var(--viz-surface-1)] p-4">
        <h2 className="text-sm font-medium text-[var(--viz-text-secondary)]">Leads by tier</h2>
        <TierBarChart data={tierCounts} />
      </section>

      <section className="mt-6 rounded-lg border border-[var(--viz-border)] bg-[var(--viz-surface-1)] p-4">
        <h2 className="text-sm font-medium text-[var(--viz-text-secondary)]">
          Conversion: targeting Serious + Quality vs. pursuing every lead
        </h2>
        <p className="mt-1 text-xs text-[var(--viz-text-muted)]">
          &ldquo;Reached disbursed&rdquo; used as the conversion proxy in this synthetic dataset.
        </p>
        <ConversionComparisonChart baselinePct={baselineConversionRate} targetedPct={targetedConversionRate} />
      </section>

      <section className="mt-6 rounded-lg border border-[var(--viz-border)] bg-[var(--viz-surface-1)] p-4">
        <h2 className="text-sm font-medium text-[var(--viz-text-secondary)]">Discipline red-flag rate by tier</h2>
        <p className="mt-1 text-xs text-[var(--viz-text-muted)]">
          Confirms risky repayers concentrate outside the Serious tier, not just get volume-chased.
        </p>
        <DisciplineFlagRateChart data={disciplineFlagRateByTier} />
      </section>
    </main>
  );
}
