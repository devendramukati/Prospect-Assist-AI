# Prospect-Assist-AI

Behavioural-analytics lead qualification and repayment-capacity assessment for retail lending (Personal / Home / Mortgage / Auto loans). See [`docs/`](docs/) for the full architecture and phased build plan.

## Monorepo layout

- `apps/web` — Next.js 15 frontend: dashboard, lead list/detail pages, and the Account Aggregator linking UI (deployed to Vercel)
- `services/scoring-service` — FastAPI backend: ingestion, categorization, income/capacity/discipline engines, scoring engine, mock core-banking/Account Aggregator integrations, audit logging (deployed to Render as a Docker container)
- `packages/synthetic-data-generator` — standalone CLI that generates synthetic customer/transaction archetypes for the MVP (no real bank data used)
- `infra` — Supabase migrations, local `docker-compose.yml`
- `render.yaml` — Render Blueprint for the scoring service (must stay at repo root)
- `tests/e2e` — cross-package smoke test: runs the real generator CLI + the real scoring service and asserts each archetype lands in its expected lead tier
- `docs` — `deployment.md`, `aws-migration-map.md`, `compliance.md`, `demo-script.md`

## Local development

**Synthetic data** (do this first — the dashboard/leads pages have nothing to show without it)

```bash
cd packages/synthetic-data-generator
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python cli.py --per-archetype 30   # writes ./data, read by the backend below
```

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

Visit `http://localhost:3000/dashboard` for the KPI/tier dashboard, or `/leads` for the scored lead list (each links to a detail page with the full score explanation and the "link another bank account" Account Aggregator flow). The home page (`/`) is just a frontend/backend health check.

## Deployment (MVP stage)

- **Frontend**: Vercel project with Root Directory set to `apps/web`.
- **Backend**: Render Blueprint (`render.yaml` at repo root) builds `services/scoring-service/Dockerfile` with the **repo root** as build context — the image bakes in a seeded dataset (210 synthetic customers, `--per-archetype 30`) from `packages/synthetic-data-generator` at build time, so the deployed service has data immediately with no manual seed step. Rebuilding regenerates a fresh (but deterministic) dataset; nothing baked in is ever real bank data.
- **Database/storage**: not provisioned for the free MVP — Supabase is skipped entirely since nothing in the code opens a connection with it yet.

See [`docs/deployment.md`](docs/deployment.md) for the full click-by-click walkthrough.

## Testing

- `services/scoring-service` and `packages/synthetic-data-generator` each have their own `pytest` suite (run `pytest` from within the package after `pip install -r requirements-dev.txt`; see `.github/workflows/ci.yml` for the exact CI invocation, and `packages/synthetic-data-generator/README.md` for that package's details).
- `tests/e2e` is a cross-package CI gate: it runs the real generator CLI and the real FastAPI service as subprocesses and asserts each archetype lands in its expected tier end-to-end. Run it with a Python environment that has both packages' dependencies installed:
  ```bash
  pip install -r tests/e2e/requirements-dev.txt
  pytest tests/e2e
  ```

## Stage 2 (AWS migration)

Each service is containerized/interface-driven so it can move independently: `services/scoring-service` → ECS Fargate, Supabase Postgres/Storage → RDS/S3, mock `CoreBankingClient`/`AAClient` adapters → real integrations. See `docs/aws-migration-map.md` (Phase 7).
