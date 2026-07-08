# Prospect-Assist-AI

Behavioural-analytics lead qualification and repayment-capacity assessment for retail lending (Personal / Home / Mortgage / Auto loans). See [`docs/`](docs/) for the full architecture and phased build plan.

## Monorepo layout

- `apps/web` — Next.js 14 frontend (deployed to Vercel)
- `services/scoring-service` — FastAPI backend: ingestion, categorization, income/capacity engine, scoring engine (deployed to Render as a Docker container)
- `packages/synthetic-data-generator` — standalone CLI that generates synthetic customer/transaction archetypes for the MVP (no real bank data used)
- `infra` — Supabase migrations, local `docker-compose.yml`
- `render.yaml` — Render Blueprint for the scoring service (must stay at repo root)
- `tests/e2e` — cross-package smoke test: runs the real generator CLI + the real scoring service and asserts each archetype lands in its expected lead tier
- `docs` — `aws-migration-map.md`, `compliance.md`, `demo-script.md`

## Local development

**Backend**

```bash
cd services/scoring-service
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Or via Docker Compose (backend + Postgres only — frontend runs natively for fast refresh):

```bash
cd infra
docker compose up --build
```

**Frontend**

```bash
cd apps/web
npm install
cp .env.example .env.local
npm run dev
```

Visit `http://localhost:3000` — it renders both the frontend status and a live health check against the scoring service at `http://localhost:8000/health`.

## Deployment (MVP stage)

- **Frontend**: Vercel project with Root Directory set to `apps/web`.
- **Backend**: Render Blueprint (`render.yaml` at repo root) builds `services/scoring-service/Dockerfile` with the **repo root** as build context — the image bakes in a seeded dataset (210 synthetic customers, `--per-archetype 30`) from `packages/synthetic-data-generator` at build time, so the deployed service has data immediately with no manual seed step. Rebuilding regenerates a fresh (but deterministic) dataset; nothing baked in is ever real bank data.
- **Database/storage**: Supabase project; apply migrations in `infra/supabase/migrations` (includes RLS policies — see `docs/compliance.md` for their current status).

## Testing

- `services/scoring-service` and `packages/synthetic-data-generator` each have their own `pytest` suite (see each package's README/CI job).
- `tests/e2e` is a cross-package CI gate: it runs the real generator CLI and the real FastAPI service as subprocesses and asserts each archetype lands in its expected tier end-to-end. Run it with a Python environment that has both packages' dependencies installed:
  ```bash
  pip install -r tests/e2e/requirements-dev.txt
  pytest tests/e2e
  ```

## Stage 2 (AWS migration)

Each service is containerized/interface-driven so it can move independently: `services/scoring-service` → ECS Fargate, Supabase Postgres/Storage → RDS/S3, mock `CoreBankingClient`/`AAClient` adapters → real integrations. See `docs/aws-migration-map.md` (Phase 7).
