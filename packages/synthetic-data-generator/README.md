# synthetic-data-generator

Standalone CLI that produces synthetic customer/bank-account/statement/funnel-event
data for the Prospect-Assist-AI MVP, since no real bank data is available. Each
customer archetype is config-driven (`config/archetypes/*.yaml`) and generation
is deterministic/seedable — regenerating with the same seed reproduces the same
data.

## Archetypes

| Archetype | Exercises |
|---|---|
| `salaried_disciplined` | fixed-salary income path, low day-1 spend velocity |
| `salaried_spend_day1` | same income path, but flags the "spends salary immediately" delinquency-risk signal |
| `gig_worker` | irregular/rolling-window income path, high income volatility |
| `business_owner_upi_heavy` | turnover→industry-margin income path, many small UPI credits |
| `window_shopper` | shallow funnel depth (low intent) despite adequate capacity |
| `strong_capacity_interested` | high capacity + funnel reaches `disbursed` (target "Serious" tier) |
| `multi_account_customer` | income split across two accounts (one `upload`, one mock-AA `aa_pull`) |

## Usage

```bash
pip install -r requirements-dev.txt
python cli.py --per-archetype 30              # writes ./data/
pytest                                         # verifies archetypes are distinguishable
```

Output layout (`data/` is gitignored — regenerate on demand):

```
data/
  manifest.json
  customers/<archetype>-<index>/
    profile.json
    accounts.json
    statements/<account_id>.json
    application_events.json
```

`statements/*.json` is what a real ingestion path (PDF upload or Account
Aggregator pull) would hand to the scoring service in Phase 2;
`application_events.json` is what a loan-origination system emits independently
of bank data, and `profile.json`/`accounts.json` mirror what a core-banking/KYC
system would supply.
