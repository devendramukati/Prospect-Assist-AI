import Link from "next/link";

import { getBackendHealth } from "@/lib/api-client";

const GOLD = "#C8952C";
const NAVY = "#0B1F3A";

const FEATURES = [
  {
    title: "Intent gate",
    body: "A prospect who only ever views an offer never gets rated Serious, however good their finances look — window-shopping is caught explicitly, not guessed at.",
  },
  {
    title: "Discipline gate",
    body: "Salary spent in full within a day of landing is detected and caps the tier below Serious — the exact early delinquency-risk pattern this track flagged.",
  },
  {
    title: "Income confidence bands",
    body: "Three separate estimation paths — fixed salary, gig/irregular, business turnover — so a business owner gets a defensible range, never a single guessed number.",
  },
  {
    title: "Account Aggregator consent",
    body: "A second bank account is linked through the RBI-regulated AA flow (request → approve → fetch), not a manual PDF upload.",
  },
];

export default async function HomePage() {
  const backendHealth = await getBackendHealth();

  return (
    <main className="mx-auto max-w-5xl px-6 py-16">
      <div className="flex flex-col items-center text-center">
        <span
          className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium"
          style={{ borderColor: "rgba(200,149,44,0.45)", color: GOLD }}
        >
          <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: GOLD }} />
          IDBI Innovate 2026 &middot; Track 02 &mdash; Lead Generation &amp; Behavioural Analytics
        </span>

        <h1 className="mt-5 text-4xl font-semibold tracking-tight">Prospect-Assist-AI</h1>
        <p className="mt-4 max-w-2xl text-[var(--viz-text-secondary)]">
          Reads a customer&apos;s bank-statement behaviour to answer the two questions a credit score alone
          can&apos;t: is this prospect genuinely interested, and can they really afford this loan &mdash; surfaced as
          an explainable Serious / Quality / Interested tier for every lead.
        </p>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/dashboard"
            className="rounded-md px-5 py-2.5 text-sm font-semibold text-white"
            style={{ backgroundColor: NAVY }}
          >
            Open Dashboard
          </Link>
          <Link
            href="/leads"
            className="rounded-md border px-5 py-2.5 text-sm font-semibold text-[var(--viz-text-primary)]"
            style={{ borderColor: "var(--viz-border)" }}
          >
            View Leads
          </Link>
        </div>
      </div>

      <section
        className="mt-14 rounded-lg border p-6"
        style={{ borderColor: "var(--viz-border)", backgroundColor: "var(--viz-surface-1)" }}
      >
        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--viz-text-muted)]">
          Track 02 problem statement
        </p>
        <p className="mt-2 text-sm text-[var(--viz-text-secondary)]">
          &ldquo;Bank&apos;s retail lending relies on traditional metrics, resulting in low conversions and limited
          insight into customer intent. A data-driven approach is needed to identify eligible, quantifiable
          repayment capacity, genuinely interested prospects using transaction and behavioral insights.&rdquo;
        </p>
        <div className="mt-4 grid grid-cols-1 gap-4 border-t pt-4 sm:grid-cols-2" style={{ borderColor: "var(--viz-border)" }}>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--viz-text-muted)]">
              Target conversion rate
            </p>
            <p className="mt-1 text-lg font-semibold">&gt; 30%</p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--viz-text-muted)]">
              Underwriting support for
            </p>
            <p className="mt-1 text-lg font-semibold">Personal &middot; Home &middot; Mortgage &middot; Auto</p>
          </div>
        </div>
      </section>

      <section className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {FEATURES.map((feature) => (
          <div
            key={feature.title}
            className="rounded-lg border p-4"
            style={{ borderColor: "var(--viz-border)", backgroundColor: "var(--viz-surface-1)" }}
          >
            <h2 className="text-sm font-semibold">{feature.title}</h2>
            <p className="mt-1.5 text-sm text-[var(--viz-text-secondary)]">{feature.body}</p>
          </div>
        ))}
      </section>

      <section className="mt-10 flex items-center justify-center gap-6 text-xs text-[var(--viz-text-muted)]">
        <span className="flex items-center gap-1.5">
          Frontend
          <span className="font-medium" style={{ color: "var(--viz-status-good)" }}>
            ok
          </span>
        </span>
        <span className="flex items-center gap-1.5">
          Scoring service
          <span
            className="font-medium"
            style={{ color: backendHealth ? "var(--viz-status-good)" : "var(--viz-status-critical)" }}
          >
            {backendHealth ? backendHealth.status : "unreachable"}
          </span>
        </span>
      </section>
    </main>
  );
}
