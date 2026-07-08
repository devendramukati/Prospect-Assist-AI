# Compliance & Security Notes (MVP scope)

This is an honest status of what's actually implemented versus what's
designed-for-later. Nothing here should be read as production-hardened —
it's the MVP-appropriate baseline the plan called for, with the seams
already in place for the real version.

## Data used

**No real customer or bank data exists anywhere in this project.** Every
customer, account, transaction, and KYC field is synthetically generated
(`packages/synthetic-data-generator`) or deterministically fabricated
(`MockCoreBankingClient`). This is true in the repo, in CI, and in the
seeded demo deployment.

## PII handling

- **Isolation by design**: the planned DB schema (`infra/supabase/migrations/0001_init.sql`)
  splits `customers` (pseudonymous: `external_ref`, `employment_type`) from
  `customer_pii` (`full_name`, `pan_masked`, `phone_masked`, `date_of_birth`).
  The entire scoring pipeline — categorization, income/capacity engines,
  discipline engine, scoring engine — operates only on the pseudonymous
  `external_ref` and never touches a PII field.
- **Masked at the source, not just in the UI**: `MockCoreBankingClient`
  (`app/integrations/core_banking/mock_client.py`) generates PAN and phone
  fields *already masked* (`XXXXX...`) — there is no raw/unmasked value
  anywhere to accidentally leak. Bank account numbers are the same:
  `masked_account_number` is masked at generation in both the synthetic
  generator and the Account Aggregator mock.
- **Verified**: a repo-wide search for unmasked PAN/account-number/Aadhaar/SSN
  fields turned up none as of Phase 7.
- **Not yet implemented**: real Supabase Auth / RLS enforcement (the
  policies in `0002_consents_and_audit_log.sql` are authored and ready but
  not applied against a live project — see below), encryption-at-rest
  configuration (inherited from whichever managed Postgres is provisioned),
  and field-level encryption for PII columns.

## Consent management (Account Aggregator)

Every consent created via `MockAAClient` carries the fields a real RBI AA
consent artifact requires: **purpose** (`purpose`), **time-bound validity**
(`expires_at`), a **specific data range** (`data_range_from`/`data_range_to`),
and an explicit **status lifecycle** (`pending → approved/denied`, plus
`expired`/`revoked` states modeled in the schema). Data is only ever pulled
after an explicit approval step — `fetch_fi_data` raises if called before
`approve_consent`. This mirrors the real consent-then-fetch flow even though
the "customer approving in their AA app" step is simulated by a button in
the demo UI rather than a second real actor.

## Explainability / model governance

Every lead score persists a factor-weighted breakdown (`app/scoring_engine/explainability.py`):
intent/capacity/discipline scores, their weights, and — critically — which
**gate** (if any) capped the tier and why (`GET /leads/{id}/explain`). This
was a deliberate design choice from Phase 4, not a retrofit: the scoring
engine is a versioned (`scoring_version`), rule-based weighted model
specifically *because* no labeled outcome data exists yet to train an ML
model on, and a rule-based model can state its reasoning in plain language
where an untrained ML model would produce an equally unjustified score with
worse transparency. See `docs/aws-migration-map.md` for how an ML model
would be introduced later without breaking this contract.

## Audit trail

`app/core/audit.py` records a structured, append-only JSON event for every
consent-lifecycle action (requested/approved/denied/fetched) and every
underwriting-report generation, including timestamp, entity, action, and an
`actor` field. **Known limitation**: there is no authenticated-user session
in this MVP, so `actor` defaults to `"system"` rather than a real loan
officer's identity — wiring that through is a Supabase-Auth-dependent
follow-up, tracked in the AWS migration map. Today these events go to
structured logs; `audit_log` (`0002_consents_and_audit_log.sql`) is the
target table for when persistence is live, using the same event shape.

## Row Level Security

`infra/supabase/migrations/0002_consents_and_audit_log.sql` adds RLS
policies for `customers`, `consents`, `audit_log`, and `customer_pii`,
scoped to two assumed JWT custom claims (`loan_officer`, `admin`) with
`customer_pii` restricted to `admin` only. **These are authored, not
tested against a live Supabase project** — no Supabase Auth is connected to
this app yet (that requires the user's Supabase account, same as the rest
of the deployment). Until a role is granted a policy, RLS's default is
deny, which is the safe failure mode.

## What a real deployment still needs before handling real bank data

1. Supabase/RDS with the above RLS policies applied and tested against real
   auth sessions.
2. Field-level encryption for `customer_pii` columns, not just RLS.
3. A real authenticated actor threaded into the audit trail.
4. A signed data-processing agreement with the licensed AA once
   `MockAAClient` is replaced with a real Sahamati-network integration.
5. A model-governance sign-off before introducing any ML-based scorer,
   consistent with RBI's fair-lending expectations for credit-adjacent
   decisioning.
