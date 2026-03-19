# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Resume Matcher: a privacy-focused recruiting tool that matches resumes against job descriptions using local or remote LLMs. Supports batch "all x all" matrix scoring with two-pass matching (standard holistic + deep criterion-by-criterion).

## Running the App

```bash
# Install deps + start on :8000 (read-only by default)
./install_and_run.sh

# Write mode (allows DB mutations)
./install_and_run.sh --write

# Smoke test (start server, hit /health, exit)
./install_and_run.sh --smoke-test

# Direct uvicorn (skip install steps)
uvicorn backend.app:app --port 8000 --reload
```

Web UI: `http://localhost:8000/` | API docs: `http://localhost:8000/docs`

System dependencies (auto-installed by launcher): `tesseract` (OCR), `poppler` (PDF).

## Architecture

FastAPI backend serving REST API and a rich HTML console.

### Backend

```
backend/
  app.py              – FastAPI app, REST endpoints (/v1/*), HTML console at /
  config.py           – Environment-driven Settings dataclass
  schemas.py          – Pydantic request/response contracts
  web_console.py      – Rich single-page HTML console (~5500 lines of inline HTML/JS)
  services/
    analysis.py       – Use-case layer: ingest JD/resume, score matches, deep scan
    repository.py     – DB adapter over database.py (CRUD for jobs/resumes/matches/runs)
    job_runner.py     – Multi-threaded durable background job executor with heartbeat
    github_sync_service.py – Auto push/pull SQLite DB to GitHub for persistence
```

### Root-level modules

- `ai_engine.py` – LLM client (OpenAI-compatible). Two-pass matching, mock mode, JSON parsing with retries.
- `database.py` – SQLite DAL with schema migrations. Tables: jobs, resumes, matches, job_runs, job_run_logs, run_matches, tags.
- `document_utils.py` – PDF/DOCX/text extraction with OCR fallback.

## Key Environment Variables

All prefixed with `RESUME_MATCHER_`:
- `LM_BASE_URL` – Model API base (default: `http://127.0.0.1:1234/v1` for LM Studio)
- `LM_API_KEY` – API key for LLM endpoint
- `LM_MODEL` – Preferred model name (auto-detect if blank)
- `DB_PATH` – SQLite file path (default: `resume_matcher.db` in project root)
- `READ_ONLY` / `WRITE_MODE` – Toggle database mutability
- `GITHUB_TOKEN` / `GITHUB_REPO` – GitHub PAT and `owner/repo` for DB sync
- `AI_CONCURRENCY` – LLM request parallelism
- `JOB_CONCURRENCY` – Simultaneous background jobs
- `LLM_TIMEOUT_SEC` – Per-request timeout (default: 600)

## Testing

No formal test framework yet. Validate with the smoke test:
```bash
./install_and_run.sh --smoke-test
```

## Development Notes

- Database is SQLite (single file, gitignored). Schema migrations run automatically on startup in `database.py`.
- The web console in `web_console.py` is a large inline HTML/JS blob served by FastAPI — not a separate frontend build.
- LLM integration uses OpenAI-compatible API format, supporting both local (LM Studio) and remote endpoints.
- The durable job runner (`job_runner.py`) persists state to `job_runs`/`job_run_logs` tables and auto-recovers after restarts.
- GitHub sync is used to persist the SQLite DB to a private GitHub repo (`my-resume-data`).
