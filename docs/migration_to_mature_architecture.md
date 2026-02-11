# Migration Plan: Streamlit -> API-First Platform

## Why this branch exists
The current implementation mixes UI and orchestration (Streamlit session state + matching flows).  
This branch introduces an API-first backbone so we can support:
- Multiple clients (web app, CLI, integrations).
- Async/background execution for larger batches.
- Cleaner separation for testing and deployment.

## What was added now (Phase 0 foundation)
- `backend/app.py`: FastAPI app with `/health` and `/v1/*` endpoints.
- `backend/schemas.py`: Pydantic request/response contracts.
- `backend/services/repository.py`: DB-facing adapter over `database.py`.
- `backend/services/analysis.py`: use-case layer for ingest + scoring workflows.
- `backend/config.py`: environment-driven config.
- `backend/services/job_runner.py`: background durable worker for queued tasks.
- `backend/web_console.py`: richer HTML console for browsing data + run logs.
- `job_runs` + `job_run_logs` tables in SQLite for durable async execution.

## Initial API surface
- `GET /health`
- `GET /v1/jobs`
- `POST /v1/jobs` (ingest text JD + tags)
- `GET /v1/resumes`
- `POST /v1/resumes` (ingest text resume + tags)
- `POST /v1/matches/score` (standard score, optional MVP deep scoring)

## Recommended next phases
1. Phase 1: Expand worker orchestration
- Move full deep-scan orchestration from Streamlit `match_flow.py` into backend jobs.
- Add batch run payloads (many JDs x many resumes) with per-item progress events.

2. Phase 2: Domain refactor
- Move core matching logic out of Streamlit-only modules (`match_flow.py`) into pure services.
- Keep Streamlit as a client to the same services to avoid duplicate business logic.

3. Phase 3: Frontend replacement
- Build a dedicated frontend (React/Next.js) against the API.
- Preserve current UX parity first, then improve workflows.

4. Phase 4: Production hardening
- Add auth (JWT/session + RBAC).
- Add structured logging + tracing.
- Add API tests + migration/versioning policy.
- Containerize and deploy with managed DB.

## Transition strategy
- No rewrite freeze: Streamlit can continue working during migration.
- New features should go into backend services first, then consumed by UI.
- Once parity is reached, Streamlit can be retired or kept as an internal admin tool.
