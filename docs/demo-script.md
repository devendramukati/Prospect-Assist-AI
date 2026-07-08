# Demo Script

A ~8-minute walkthrough proving the two core asks from the problem statement:
(1) separate genuinely interested prospects from window-shoppers, and (2) assess
real repayment capacity from behavioural data, including catching a
"spends the salary on day 1" delinquency-risk pattern. Everything below runs
against synthetic data — no real bank data is used anywhere.

## Setup (before presenting)

```bash
# 1. Generate a demo dataset (~30 customers/archetype = 210 total)
cd packages/synthetic-data-generator
python cli.py --per-archetype 30 --seed demo

# 2. Start the backend (from services/scoring-service)
uvicorn app.main:app --reload

# 3. Start the frontend (from apps/web)
npm run dev
```

Open `http://localhost:3000/dashboard`.

## 1. The dashboard (1 min)

- **Point to the KPI row**: total leads, how many are Serious+Quality (the
  targeted segment), and the discipline red-flag count.
- **Point to "Leads by tier"**: the bank doesn't get one undifferentiated
  pile of prospects — it gets four ranked tiers.
- **Point to the conversion comparison chart**: pursuing only Serious+Quality
  leads converts at a meaningfully higher rate than treating every lead the
  same — this is the >30%-conversion claim made concrete and computed, not
  asserted.
- **Point to the discipline red-flag-rate-by-tier chart**: 0% of Serious-tier
  leads carry a discipline red flag — *by construction* of the scoring gate,
  not by luck. This is the direct answer to "how do we avoid chasing
  volume over quality."

## 2. The window-shopper problem (2 min)

Go to `/leads`, filter to **Interested**, open a `window_shopper-*` customer.

- Point to the **income and capacity numbers** — they look fine. Good salary,
  healthy disposable income.
- Point to **"Why this score"**: the **Intent** bar is tiny (≈0.10) next to
  strong Capacity/Discipline bars.
- Point to the **gate reason** in red: *"Never progressed past viewing an
  offer — capped below Quality/Serious regardless of finances."*
- **The story**: this customer looks fine on paper and would have consumed
  relationship-manager effort under the old approach. The system correctly
  down-ranks them because they never actually started an application —
  intent, not just eligibility, drives the tier.

## 3. The delinquency-risk problem (2 min)

Go back to `/leads`, open a `salaried_spend_day1-*` customer (tier: **Quality**,
not Serious).

- Point to **Discipline signals**: day-1 spend velocity ~70%, meaning most of
  the salary leaves the account within 2 days of landing — this is the exact
  pattern from the problem statement ("salary credited, immediately spends
  entire amount").
- Point to **"Why this score"**: Intent and Capacity are both strong (0.85,
  0.89), but the composite is still capped.
- Point to the **gate reason**: *"Discipline red flag (bounced payment or
  high day-1 spend velocity) — capped below Serious."*
- **The story**: good income alone doesn't make a good borrower. The system
  catches a real repayment-discipline signal that traditional
  eligibility-only underwriting would miss entirely.

## 4. Business-owner income assessment (1.5 min)

Open a `business_owner_upi_heavy-*` customer.

- Point to **Income**: shown as a **confidence band** (low–mid–high), not a
  single hard number, with the method labeled "Turnover × industry margin."
- Point to the note under Repayment capacity: *"Assessed against business
  turnover/cash flow, not the personal net-income figure shown above."*
- **The story**: a shopkeeper's UPI receipts aren't personal income — the
  system derives a defensible income estimate from turnover and an
  industry-margin benchmark, and is honest about the uncertainty instead of
  presenting a single number as if it were as certain as a salary slip.

## 5. Multi-account cross-check (1.5 min)

Open a **single-account** customer (e.g. `salaried_disciplined-000`), note the
current income figure, then click **"Link another bank account via Account
Aggregator."**

- Walk through the modal: select a bank → **Request consent** (shows purpose,
  date range, expiry — a real consent artifact, not just a checkbox) →
  **Simulate customer approval** (stands in for the customer's AA app) →
  **Fetch account data**.
- Close and refresh: **Accounts (2)**, and the income/disposable-income/
  affordability figures visibly increase.
- **The story**: this is the RBI-regulated, consent-based way to cross-check
  a customer's other accounts — the realistic alternative to "ask the
  customer to email another PDF" the problem statement raised.

## 6. Underwriting export (30 sec)

Click **"Download underwriting summary (JSON)"** on any customer — show it's
a clean, loan-officer-readable document (income band, FOIR, affordability by
product, risk flags, tier, and the full factor explanation), not the raw
internal API response shape.

## Closing point

Every score is explainable (factor breakdown + gate reasons), every
Account Aggregator pull is consent-gated and audited, and every integration
point (ingestion, AA, core banking) sits behind an interface so the same
scoring pipeline runs unchanged once real bank data and AWS infrastructure
replace the synthetic/mock layer — see `docs/aws-migration-map.md`.
