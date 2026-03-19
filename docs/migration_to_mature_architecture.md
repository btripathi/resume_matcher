# Migration Plan: Streamlit -> API-First Platform

## Status
**Phases 0-2 complete.** Streamlit code has been removed. The FastAPI backend with HTML console is the sole UI.

## What was built (Phase 0-2)
- `backend/app.py`: FastAPI app with `/health` and `/v1/*` endpoints.
- `backend/schemas.py`: Pydantic request/response contracts.
- `backend/services/repository.py`: DB-facing adapter over `database.py`.
- `backend/services/analysis.py`: use-case layer for ingest + scoring workflows.
- `backend/config.py`: environment-driven config.
- `backend/services/job_runner.py`: background durable worker for queued tasks.
- `backend/web_console.py`: rich HTML console for browsing data + run logs.
- `job_runs` + `job_run_logs` tables in SQLite for durable async execution.
- Deep-scan orchestration moved into backend jobs.
- Core matching logic lives in pure services.

## Remaining phases

### Phase 3: Frontend replacement
- Build a dedicated frontend (React/Next.js) against the API.
- Preserve current UX parity first, then improve workflows.

### Phase 4: Production hardening
- Add auth (JWT/session + RBAC).
- Add structured logging + tracing.
- Add API tests + migration/versioning policy.
- Containerize and deploy with managed DB.
