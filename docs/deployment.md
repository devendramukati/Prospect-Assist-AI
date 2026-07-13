# Deploying the free MVP (Render + Vercel)

Step-by-step walkthrough for putting the live prototype online at zero cost. No Supabase step — it's skipped entirely, since nothing in the code connects to it yet (see `app/core/config.py`: `database_url`/`supabase_url` are read but never used to open a connection).

Two services to deploy, in this order (backend first, since the frontend needs its URL):

1. **Backend** (`services/scoring-service`) → Render, free Docker web service
2. **Frontend** (`apps/web`) → Vercel, free Hobby plan

---

## 0. Prerequisites

- Code is already pushed to `https://github.com/devendramukati/Prospect-Assist-AI` — nothing to do here.
- A free [Render](https://render.com) account, signed up via GitHub (so it can access the repo).
- A free [Vercel](https://vercel.com) account, signed up via GitHub.

---

## 1. Deploy the backend on Render

1. Render dashboard → **New +** → **Blueprint**.
2. Connect the `devendramukati/Prospect-Assist-AI` repo. Render auto-detects `render.yaml` at the repo root — it already defines the service (`prospect-assist-scoring-service`, Docker runtime, `services/scoring-service/Dockerfile`, free plan), so you don't hand-configure the build.
3. Render will prompt you to fill in the env vars marked `sync: false` in `render.yaml`. Fill them in as follows:
   - `CORS_ALLOW_ORIGINS` — leave as `http://localhost:3000` for now; you'll come back and update this in step 3 once the Vercel URL exists.
   - `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` — leave **blank**. Nothing in the app reads these at startup or opens a connection with them; they exist in the schema for the future Supabase wiring, not for anything live today.
4. Click **Apply** / **Deploy**. The build:
   - installs `services/scoring-service/requirements.txt`
   - installs `packages/synthetic-data-generator/requirements.txt` and runs its CLI (`--per-archetype 30 --seed prod-seed`), baking **210 synthetic customers** into the image so the API has data the moment it boots — no manual seed step
   - starts `uvicorn app.main:app` on port 8000

   First build takes a few minutes (Docker layer install + data generation). Watch the Render build log for `Generated 210 synthetic customers across 7 archetypes` — that confirms the bake-in step ran.

5. Once live, Render gives you a URL like `https://prospect-assist-scoring-service.onrender.com`. Verify it:
   ```
   curl https://prospect-assist-scoring-service.onrender.com/health
   curl https://prospect-assist-scoring-service.onrender.com/leads
   ```
   `/health` should return `{"status":"ok","service":"scoring-service"}`; `/leads` should return `"count":210` and a list.

**Keep this URL** — you need it for step 2.

---

## 2. Deploy the frontend on Vercel

1. Vercel dashboard → **Add New** → **Project** → import the same GitHub repo.
2. **Root Directory**: set to `apps/web` (this repo is a monorepo — Vercel must build only the frontend package, not the whole repo). Framework preset auto-detects as Next.js.
3. **Environment Variables** — add these (values from `apps/web/.env.example`, pointed at your Render URL from step 1 instead of localhost):
   | Key | Value |
   |---|---|
   | `SCORING_SERVICE_URL` | `https://prospect-assist-scoring-service.onrender.com` (your Render URL, no trailing slash) |
   | `NEXT_PUBLIC_SCORING_SERVICE_URL` | same Render URL |
   | `NEXT_PUBLIC_SUPABASE_URL` | leave blank |
   | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | leave blank |

   Both `SCORING_SERVICE_URL` variants are needed: the plain one is read server-side (`lib/api-client.ts`, used by the Server Components that fetch `/leads` and `/leads/{ref}/explain`), the `NEXT_PUBLIC_` one is read client-side (`LinkAccountModal.tsx`, which calls the Account Aggregator endpoints directly from the browser).
4. **Deploy**. Vercel gives you a URL like `https://prospect-assist-ai.vercel.app`.

---

## 3. Close the CORS loop

The backend's `CORSMiddleware` only allows origins listed in `CORS_ALLOW_ORIGINS` (`app/main.py`) — with it still set to `http://localhost:3000`, the deployed frontend's requests will be blocked by the browser.

1. Go back to the Render service → **Environment**.
2. Update `CORS_ALLOW_ORIGINS` to your Vercel URL from step 2, e.g. `https://prospect-assist-ai.vercel.app` (comma-separate if you also want to keep `http://localhost:3000` for local dev against the deployed backend).
3. Save — Render redeploys automatically (no rebuild needed, just a restart with the new env var).

---

## 4. Verify end-to-end

Visit `https://<your-vercel-url>/dashboard` — you should see the KPI tiles and charts populated from the 210 baked-in customers. Open `/leads`, click into a lead, and try "Link another bank account via Account Aggregator" to confirm the client-side calls reach Render too (open browser dev tools → Network tab if anything looks blank — a CORS error there means step 3 wasn't saved/redeployed yet).

---

## Free-tier caveats worth knowing before a live demo

- **Render free web services sleep after ~15 minutes of inactivity** and take tens of seconds to cold-start on the next request. Before a judging/demo session, hit the Render `/health` URL once a minute or two ahead of time to warm it up — otherwise the first dashboard load in front of judges will hang.
- **Vercel Hobby plan** has no such sleep behavior (serverless, always warm), so the frontend itself loads instantly — it's specifically the Render backend that needs the pre-warm.
- Rebuilding the Render service regenerates the 210 synthetic customers fresh (same seed, so deterministic) — this is expected, not a bug, and nothing generated is ever real bank data.
- No database is provisioned in this deployment — data lives only in the Docker image's in-memory/file-backed synthetic dataset and resets on every redeploy. That's consistent with "prototype stage, no real backing store" and matches what's already documented in the README's Deployment section.
