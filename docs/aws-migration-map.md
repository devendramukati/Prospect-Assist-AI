# AWS Migration Map

This MVP was deliberately built on free-tier services (Vercel, Render, Supabase)
so it could ship fast without waiting on an AWS Sandbox. Every component was
chosen so this stage-2 migration is a **backend swap behind an existing
interface**, not a rewrite. Nothing below has been provisioned — this is the
target architecture for when AWS Sandbox access is granted.

## Component-by-component mapping

| MVP component | MVP implementation | AWS target | Migration shape |
|---|---|---|---|
| Frontend | Next.js 15 on Vercel | Same (Vercel), or Amplify Hosting / S3+CloudFront if the bank mandates single-cloud | Config change only |
| Backend API | FastAPI in a Docker container on Render | **ECS Fargate** (or EKS) behind an ALB/API Gateway | Same Docker image — `render.yaml` becomes a task definition |
| Database | Supabase Postgres | **RDS/Aurora Postgres** | `pg_dump`/`pg_restore` or DMS; same schema (`infra/supabase/migrations`) |
| File/object storage | Supabase Storage | **S3** | Same bucket-style API |
| Auth | Supabase Auth (not yet wired into the app) | **Cognito** | Re-point the auth client; RLS policies (`0002_consents_and_audit_log.sql`) map to Cognito custom claims the same way they assume Supabase JWT claims today |
| Ingestion (synthetic/local) | `SyntheticFileIngestionSource` reading generated JSON files | `PdfUploadIngestionSource` backed by **Textract** (statement OCR) | Same `IngestionSource` interface (`app/ingestion/base.py`); only the concrete class changes |
| Account Aggregator integration | `MockAAClient`, in-memory consent store | Real Sahamati-network licensed AA (Finvu/OneMoney/CAMSFinserv/Anumati) + `consents` table in RDS | Same `AAClient` interface (`app/integrations/account_aggregator/base.py`) |
| Core banking integration | `MockCoreBankingClient`, fabricated KYC | Real Finacle/Flexcube/BaNCS adapter via API Gateway/PrivateLink | Same `CoreBankingClient` interface |
| Lead scoring | Rule-based weighted scorer (`app/scoring_engine`), versioned YAML weights | Same rule engine as an explainability baseline, or **XGBoost/LightGBM + SHAP** served via **SageMaker** once real labeled outcomes exist | New `Scorer` implementation behind the same composite-score contract |
| Audit trail | Structured JSON logs (`app/core/audit.py`) | Same log shape shipped to **CloudWatch Logs**, or written directly to the `audit_log` table | Swap the sink, keep the event schema |
| CI/CD | GitHub Actions → Vercel/Render deploy hooks | Same GitHub Actions, or CodePipeline/CodeBuild if the bank wants native AWS CI | No app code change |
| Secrets | `.env` / Vercel/Render project env vars | **Secrets Manager** | Config change only |

## What doesn't need to change

Every integration point above was built behind an abstract interface
specifically so this list would be short:

- `app/ingestion/base.py` — `IngestionSource`
- `app/integrations/account_aggregator/base.py` — `AAClient`
- `app/integrations/core_banking/base.py` — `CoreBankingClient`
- The income/capacity/discipline/scoring engines never touch a data source
  directly — they only consume the `Transaction`/`ApplicationEvent`/
  `CustomerBundle` domain models (`app/models/domain.py`), regardless of
  where those came from.

## Sequencing recommendation

1. Stand up RDS Postgres and apply `infra/supabase/migrations/*.sql` as-is
   (they're plain Postgres, not Supabase-specific SQL).
2. Move file storage to S3; keep `SyntheticFileIngestionSource` pointed at
   an S3-backed path during the transition (or ship the small adapter change
   to read from S3 instead of local disk — same interface).
3. Stand up Cognito, re-point auth, verify the RLS policies against real JWT
   claims before removing the "no policy = denied" fallback.
4. Replace `MockAAClient`/`MockCoreBankingClient` with real integrations one
   at a time — the interface boundary means the scoring pipeline doesn't
   need to change while that happens.
5. Only after real labeled conversion/default outcomes exist, introduce an
   ML-based `Scorer` alongside the rule-based one (shadow-score first, don't
   cut over blind).
