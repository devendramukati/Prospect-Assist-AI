import { notFound } from "next/navigation";

import { Meter } from "@/components/Meter";
import { TierBadge } from "@/components/TierBadge";
import { getLeadExplain, getUnderwritingReportUrl } from "@/lib/api-client";

import { ScoreFactorChart } from "./components/ScoreFactorChart";

const METHOD_LABEL: Record<string, string> = {
  fixed_salary: "Fixed salary",
  rolling_avg: "Rolling average (irregular income)",
  turnover_margin: "Turnover × industry margin",
};

const PRODUCT_LABEL: Record<string, string> = {
  personal_loan: "Personal loan",
  auto_loan: "Auto loan",
  home_loan: "Home loan",
  mortgage_loan: "Mortgage loan",
};

function inr(amount: number): string {
  return `₹${Math.round(amount).toLocaleString("en-IN")}`;
}

export default async function LeadDetailPage({ params }: { params: Promise<{ externalRef: string }> }) {
  const { externalRef } = await params;
  const data = await getLeadExplain(externalRef);

  if (!data) {
    notFound();
  }

  const { customer, assessment, score } = data;
  const foirPct = assessment.disposable_income.foir_pct * 100;
  const foirStatus = foirPct < 40 ? "good" : foirPct < 55 ? "warning" : "serious";

  return (
    <main className="mx-auto max-w-3xl p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{customer.external_ref}</h1>
          <p className="text-sm text-[var(--viz-text-secondary)]">{customer.employment_type}</p>
        </div>
        <TierBadge tier={score.tier} />
      </div>

      <section className="mt-6 rounded-lg border border-[var(--viz-border)] bg-[var(--viz-surface-1)] p-4">
        <h2 className="text-sm font-medium text-[var(--viz-text-secondary)]">Income</h2>
        <p className="mt-2 text-xl font-semibold">{inr(assessment.income.monthly_income_estimate)}/mo</p>
        <p className="text-xs text-[var(--viz-text-muted)]">
          {METHOD_LABEL[assessment.income.method] ?? assessment.income.method} &middot; stability{" "}
          {assessment.income.income_stability_score.toFixed(2)}
        </p>
        {assessment.income.confidence_low !== null && assessment.income.confidence_high !== null ? (
          <p className="mt-1 text-xs text-[var(--viz-text-muted)]">
            Confidence band: {inr(assessment.income.confidence_low)} &ndash; {inr(assessment.income.confidence_high)}
          </p>
        ) : null}
      </section>

      <section className="mt-6 rounded-lg border border-[var(--viz-border)] bg-[var(--viz-surface-1)] p-4">
        <h2 className="text-sm font-medium text-[var(--viz-text-secondary)]">Expense breakdown (avg/mo)</h2>
        <dl className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-xs text-[var(--viz-text-muted)]">Essential needs</dt>
            <dd className="[font-variant-numeric:tabular-nums]">{inr(assessment.expense_summary.essential_needs)}</dd>
          </div>
          <div>
            <dt className="text-xs text-[var(--viz-text-muted)]">Compulsory obligations</dt>
            <dd className="[font-variant-numeric:tabular-nums]">
              {inr(assessment.expense_summary.compulsory_obligations)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-[var(--viz-text-muted)]">Discretionary</dt>
            <dd className="[font-variant-numeric:tabular-nums]">
              {inr(assessment.expense_summary.discretionary_wants)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-[var(--viz-text-muted)]">Savings / investment</dt>
            <dd className="[font-variant-numeric:tabular-nums]">
              {inr(assessment.expense_summary.savings_investment)}
            </dd>
          </div>
        </dl>
      </section>

      <section className="mt-6 rounded-lg border border-[var(--viz-border)] bg-[var(--viz-surface-1)] p-4">
        <h2 className="text-sm font-medium text-[var(--viz-text-secondary)]">Repayment capacity</h2>
        <div className="mt-3">
          <Meter label="FOIR (existing obligations / income)" valuePct={foirPct} status={foirStatus} />
        </div>
        <p className="mt-3 text-sm">
          Disposable income: <span className="font-medium">{inr(assessment.disposable_income.disposable_income)}/mo</span>
        </p>
        {assessment.capacity_basis === "turnover" ? (
          <p className="mt-1 text-xs text-[var(--viz-text-muted)]">
            Assessed against business turnover/cash flow, not the personal net-income figure shown above.
          </p>
        ) : null}

        <table className="mt-4 w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-[var(--viz-border)] text-left text-xs uppercase tracking-wide text-[var(--viz-text-muted)]">
              <th className="py-2 pr-3 font-medium">Product</th>
              <th className="py-2 px-3 font-medium text-right">Max EMI</th>
              <th className="py-2 px-3 font-medium text-right">Max principal</th>
              <th className="py-2 pl-3 font-medium">Notes</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(assessment.affordability_by_product).map(([product, affordability]) => (
              <tr key={product} className="border-b border-[var(--viz-border)] last:border-0">
                <td className="py-2 pr-3">{PRODUCT_LABEL[product] ?? product}</td>
                <td className="py-2 px-3 text-right [font-variant-numeric:tabular-nums]">
                  {inr(affordability.max_affordable_emi)}
                </td>
                <td className="py-2 px-3 text-right [font-variant-numeric:tabular-nums]">
                  {inr(affordability.max_affordable_principal)}
                </td>
                <td className="py-2 pl-3 text-xs text-[var(--viz-text-muted)]">
                  {affordability.requires_collateral_input ? "Requires property value/LTV input" : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="mt-6 rounded-lg border border-[var(--viz-border)] bg-[var(--viz-surface-1)] p-4">
        <h2 className="text-sm font-medium text-[var(--viz-text-secondary)]">Discipline signals</h2>
        <ul className="mt-3 space-y-1 text-sm">
          <li>
            Day-1 spend velocity:{" "}
            <span className="font-medium">
              {(assessment.discipline.day1_spend_velocity.day1_spend_velocity_pct * 100).toFixed(0)}%
            </span>{" "}
            of top credits spent within 2 days
          </li>
          <li>
            Bounced payments: <span className="font-medium">{assessment.discipline.bounce.bounce_count}</span>
          </li>
          <li>
            Balance went negative:{" "}
            <span className="font-medium">{assessment.discipline.balance.went_negative ? "Yes" : "No"}</span>
          </li>
        </ul>
      </section>

      <section className="mt-6 rounded-lg border border-[var(--viz-border)] bg-[var(--viz-surface-1)] p-4">
        <h2 className="text-sm font-medium text-[var(--viz-text-secondary)]">Why this score</h2>
        <ScoreFactorChart factors={score.explanation.factors} />
        {score.explanation.gate_reasons.length > 0 ? (
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm" style={{ color: "var(--viz-status-serious)" }}>
            {score.explanation.gate_reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        ) : null}
      </section>

      <a
        href={getUnderwritingReportUrl(externalRef)}
        target="_blank"
        rel="noreferrer"
        className="mt-6 inline-block text-sm underline text-[var(--viz-text-secondary)]"
      >
        Download underwriting summary (JSON)
      </a>
    </main>
  );
}
