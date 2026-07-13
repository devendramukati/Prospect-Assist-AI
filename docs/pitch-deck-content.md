# IDBI Innovate 2026 — Prototype Submission Deck Content

Slide-by-slide content for `Prototype Submission Deck _ IDBI Innovate.pdf`, written only from what's actually built and verified in this repo. Anything I can't verify (video link, live deployment URL, cost figures) is flagged as **TBD** rather than invented.

---

## Slide 1 — Team Details
Already filled in the template:
- Team name: Individual
- Team leader name: Devendra Mukati
- Problem Statement: Prospect Assist AI (Track 2)

---

## Slide 2 — Brief about the idea

> Retail lending teams today qualify prospects mostly on stated income and credit-bureau eligibility. That tells you almost nothing about whether someone is genuinely going to convert, or whether they can actually service a new EMI once you look at how they really spend, save, and repay. Prospect-Assist-AI reads a customer's bank statement transaction history — and, with their explicit consent, a second linked account — to answer the two questions a credit score alone can't: **is this person actually interested**, and **can they really afford this loan**?
>
> It categorizes every transaction into essential needs, existing obligations, discretionary spend, and savings; estimates income differently for a salaried employee, a gig worker, and a business owner; and produces an explainable Serious / Quality / Interested / Not-Qualified tier for every lead — so relationship managers spend their time on the leads worth chasing, and underwriters get a real repayment-capacity view that income-only eligibility checks would miss entirely.

*(~130 words — trim if the slide needs it shorter.)*

---

## Slide 3 — Opportunities

**How is it different from other existing ideas?**
Most lead-scoring tools work off CRM/demographic data or a bureau score — a single number with no visibility into *why*. Prospect-Assist-AI works off the same evidence a human underwriter would manually dig through (transaction narrations, spend timing, recurring debits) and turns it into a structured, explainable signal automatically. It doesn't need clickstream or app-analytics infrastructure to measure intent, either — it derives that from the loan-application funnel itself (viewed offer → started application → disbursed), which every bank's loan origination system already emits.

**How will it solve the problem?**
- *Genuine interest vs. window-shopping*: a customer who repeatedly checks eligibility but never starts an application is capped below Quality/Serious by an explicit **intent gate**, regardless of how good their finances look.
- *Real repayment capacity, not stated income*: three separate income-estimation paths (fixed-salary, gig/irregular, business turnover) plus a FOIR/affordability calculation per loan product (Personal, Auto, Home, Mortgage).
- *Catching the exact delinquency pattern you flagged*: a customer whose salary leaves the account within a day of landing is caught by a **discipline gate** and capped below Serious — independent of how much they earn.
- *Multi-account cross-check, done properly*: instead of asking a customer to email another bank's PDF statement, the system uses the RBI-regulated **Account Aggregator** consent flow — request → customer approval → consented data pull — to consolidate a second account into one capacity assessment.

**USP of the proposed solution**
Every score comes with a plain-language, factor-weighted explanation and a named gate reason — never a black box, which matters for a lending decision. The whole pipeline is built behind clean interfaces (ingestion, Account Aggregator client, core-banking client), so the exact same scoring code that runs on synthetic data today runs unchanged once real bank statements, a real AA integration, and real core-banking data are plugged in — no rewrite between prototype and production.

---

## Slide 4 — List of features offered by the solution

1. **Synthetic bank-statement generator** — 7 realistic customer archetypes (disciplined salaried, salary-spent-on-day-1, gig worker, business owner, window-shopper, strong-capacity, multi-account) for demoing without any real customer data.
2. **Rule-based transaction categorization** — income / essential needs / compulsory obligations / discretionary / savings / bank charges, plus a recurring-transaction detector that identifies salary and EMI/rent automatically.
3. **Employment-aware income engine** — fixed-salary (median + stability score), gig/irregular (recency-weighted, volatility-discounted), and business-owner (turnover × industry-margin band, reported as a confidence range, not a single guessed number).
4. **Repayment-capacity engine** — FOIR and disposable income, plus max-affordable-EMI/principal per loan product; Home/Mortgage are correctly flagged as needing a property-value input the bank statement alone can't supply.
5. **Discipline engine** — day-1 spend-velocity detection, bounced-payment detection, and low/negative-balance detection.
6. **Explainable lead-scoring engine** — a versioned, weighted composite score with two hard gates (never-started-an-application; discipline red flag) so a lead can't be rated Serious on income alone.
7. **Lead dashboard** — KPI tiles, tier breakdown, a baseline-vs-targeted conversion comparison, and a discipline-red-flag-rate-by-tier chart, computed live from the scored leads.
8. **Lead list & detail pages** — sortable/filterable table; a detail view with income breakdown, a FOIR meter, an affordability table, and a full "why this score" explanation panel.
9. **Account Aggregator consent flow** — request → approve → fetch, modeled on the real RBI-regulated flow, with the customer's capacity assessment updating live once a second account is linked.
10. **Mock core-banking KYC lookup** — surfaces the customer's name/PAN on the lead record the way a real core-banking integration would.
11. **Underwriting-summary export** — a clean, loan-officer-readable JSON report per customer (income band, FOIR, affordability, risk flags, tier, full explanation).
12. **Audit logging** — every consent action and underwriting-report generation recorded as a structured, timestamped, append-only event.
13. **CI-gated regression testing** — 100+ automated tests, including a cross-package smoke test that runs the real data generator and the real API together and checks every archetype lands in its expected tier before anything ships.

---

## Slide 5 — Process flow diagram / Use-case diagram

**File**: `docs/diagrams/process-flow.drawio` (open in [draw.io](https://app.diagrams.net))

Shows the full pipeline: transaction data → ingestion & categorization → employment-aware income routing (salaried / gig / business owner) → capacity engine → discipline engine → composite scoring (combined with the intent engine) → the two explainability gates → final tier → RM dashboard / underwriting export — plus the Account Aggregator consent side-flow that can merge a second account in at any point.

---

## Slide 6 — Wireframes/Mock diagrams (optional)

**Skipped by design.** The prototype went straight to a working UI (Next.js dashboard, lead list, lead detail, Account Aggregator modal) rather than a separate wireframe stage — the real product screenshots on Slide 10 are used instead; they're more convincing than a mockup for a working prototype submission.

---

## Slide 7 — Architecture diagram of the proposed solution

**File**: `docs/diagrams/architecture-current.drawio` — the actual deployed shape: Next.js on Vercel, FastAPI on Render (Docker), the engine modules, mock Account Aggregator/core-banking integrations, and Supabase shown explicitly as *not yet connected* (honest, not hidden).

Optionally pair it with `docs/diagrams/architecture-future.drawio` (AWS stage-2 target: ECS Fargate, RDS, Cognito, Textract, SageMaker) on Slide 12 to show the growth path.

---

## Slide 8 — Technologies to be used in the solution

**Frontend**: Next.js 15 (App Router, TypeScript), Tailwind CSS, Recharts — deployed on Vercel.

**Backend**: Python 3.11, FastAPI, Pydantic — deployed as a Docker container on Render.

**Data (prototype stage)**: a custom synthetic bank-statement/transaction generator — **no real bank data is used anywhere in this submission.**

**Testing & CI**: pytest, ruff, GitHub Actions (per-package CI plus a cross-package end-to-end regression gate).

**Integrations (built behind real interfaces, mocked for the prototype)**: RBI Account Aggregator consent flow; core-banking KYC lookup — both designed so a real integration drops in without changing the scoring pipeline.

**Target cloud (stage 2, not yet provisioned)**: AWS — ECS Fargate, RDS/Aurora Postgres, S3, Cognito, Textract (statement OCR), SageMaker (future ML-based scorer, introduced only once real labeled outcomes exist). See `docs/aws-migration-map.md`.

---

## Slide 9 — Estimated implementation cost (optional)

**Prototype stage: ₹0 / $0.** Built and run entirely on free tiers — Vercel Hobby, Render free web service, GitHub Actions free CI minutes. No paid infrastructure was used to build or demo this submission.

**Stage 2 (AWS): to be estimated once AWS Sandbox access is granted.** Cost would scale with real transaction/statement volume (ECS Fargate compute, RDS storage, Textract per-page OCR pricing, SageMaker training/inference) — I'd rather give you a real number once real usage patterns (customer count, statement volume, request rate) are known than guess one now.

---

## Slide 10 — Snapshots of the prototype

Real screenshots of the running prototype (Next.js frontend + FastAPI backend, both running locally against a freshly generated 210-customer synthetic dataset), captured under `docs/screenshots/`:

1. **`01-dashboard.png`** — Relationship Manager Dashboard: KPI tiles (210 total leads, 179 Serious+Quality, avg composite score 0.76, 46 discipline red flags), the leads-by-tier bar chart, the baseline-vs-targeted conversion comparison (28.6% vs 33.5%), and the discipline-red-flag-rate-by-tier chart.
2. **`02-leads-list.png`** — Prospect Leads table: sortable, tier-filterable, ranked by composite score, with the persistent navy/gold navigation header (active "Leads" tab highlighted).
3. **`03-lead-detail-window-shopper.png`** — `window_shopper-000`: strong capacity (0.83) and reasonable discipline (0.70) but intent only 0.10 — capped at **Interested** by the intent gate, with the gate reason spelled out under "Why this score."
4. **`04-lead-detail-discipline-flag.png`** — `salaried_spend_day1-000`: strong intent (0.85) and capacity (0.89), but 70% of top credits spent within 2 days plus 1 bounced payment — capped at **Quality** (below Serious) by the discipline gate. This is the exact "spends the whole salary on day 1" pattern flagged as a delinquency-risk concern.
5. **`05-lead-detail-income-confidence-band.png`** — `business_owner_upi_heavy-000`: income shown as `Turnover × industry margin` with an explicit confidence band (₹75,894–₹1,32,814/mo), not a single guessed number.
6. **`06-aa-consent-pending.png`** — Account Aggregator modal mid-flow: consent requested from HDFC Bank, showing the data-range, purpose, and expiry, waiting on simulated customer approval.
7. **`07-aa-linked-completed.png`** — Account Aggregator modal after approval + fetch: second account linked, capacity assessment now includes it (`Accounts (2)` on the lead detail page).

---

## Slide 11 — Prototype Performance report/Benchmarking

All figures below are from actual runs during development on **synthetic data** — labeled honestly as prototype-stage validation, not a production load test (no formal load/concurrency testing has been done).

- **108 automated tests passing** (95 backend + 9 synthetic-data-generator + 4 cross-package end-to-end), re-verified right before writing this deck. The end-to-end suite runs the real data generator and the real API together and asserts every one of the 7 customer archetypes lands in its expected lead tier.
- **From an actual 210-customer run** (30 per archetype, freshly generated and scored to write this slide, and re-verified again when capturing the Slide 10 screenshots): 90 Serious, 89 Quality, 31 Interested, 0 Not Qualified.
- **Discipline red-flag rate by tier**: 0 of the 90 Serious-tier leads carried a discipline red flag (46 flags total across the other 210) — *by construction* of the scoring gate, not by chance.
- **Conversion-proxy comparison**: targeting only Serious+Quality leads showed a "reached disbursed" rate of 33.5%, versus 28.6% if every lead were pursued equally. This number moves with the random seed and archetype mix used to generate the demo data, so treat it as a representative example from synthetic data, not a guaranteed real-world figure.
- **API responsiveness (local, unoptimized, anecdotal)**: individual endpoint calls completed in roughly 70–150ms per customer during smoke testing — not a formal load-test benchmark, just a development-time observation.

---

## Slide 12 — Additional Details/Future Development

- Replace the mock Account Aggregator and core-banking clients with real integrations — the interfaces are already designed for this swap with no change to the scoring pipeline.
- Introduce a real ML-based scorer (e.g., XGBoost/LightGBM with SHAP explanations) **in shadow mode only, once real labeled conversion/default outcomes exist** — the rule-based engine stays primary until then, for explainability and fair-lending reasons.
- Move from file-based synthetic ingestion to real PDF bank-statement ingestion via Amazon Textract, behind the same ingestion interface.
- Add real persistence (Postgres via Supabase/RDS) for consents and the audit trail — the schema and Row-Level Security policies are already drafted (`infra/supabase/migrations/`), just not yet applied to a live database.
- Add authenticated loan-officer/admin roles (Cognito or Supabase Auth) so the audit trail records a real actor instead of "system."
- See `docs/aws-migration-map.md` for the full stage-2 sequencing plan.

---

## Slide 13 — Links

- **GitHub Public Repository**: https://github.com/devendramukati/Prospect-Assist-AI
- **Demo Video Link (3 minutes)**: **TBD** — I can't record video myself, but `docs/demo-script.md` is already written as a ready-to-follow 3-minute walkthrough script (dashboard → window-shopper example → delinquency-risk example → business-owner income band → Account Aggregator linking → underwriting export). Recording against that script should take one take.
- **Final Product Link**: **TBD** — pending your Vercel + Render deployment. Let me know once it's live and I'll verify both URLs before you put them on the slide.

---

## Slide 14 — (blank divider in template, no content needed)

## Slide 15 — Thank you (template slide, no content needed)
