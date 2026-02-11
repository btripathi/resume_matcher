import os
import urllib.request

from fastapi import FastAPI, HTTPException
from openai import OpenAI

from ai_engine import AIEngine
from database import DBManager

from .config import settings
from .schemas import (
    HealthResponse,
    JobIn,
    JobOut,
    MatchOut,
    RunLogOut,
    RunOut,
    RunRequest,
    ResumeIn,
    ResumeOut,
    ScoreMatchRequest,
)
from .services.analysis import AnalysisService
from .services.github_sync_service import GitHubSyncService
from .services.job_runner import JobRunner
from .services.repository import Repository
from .web_console import render_console


DEFAULT_CLOUD_URL = "https://equitably-unmetalized-frieda.ngrok-free.dev/v1"
DEFAULT_LOCAL_URL = "http://127.0.0.1:1234/v1"


def _check_local_lm_available() -> bool:
    try:
        with urllib.request.urlopen(DEFAULT_LOCAL_URL + "/models", timeout=0.5) as resp:
            return 200 <= int(resp.status) < 400
    except Exception:
        return False


def create_app() -> FastAPI:
    app = FastAPI(
        title="Resume Matcher API",
        version="0.1.0",
        description="Backend-first API for resume matching workflows.",
    )

    db = DBManager(db_path=settings.db_path)
    repo = Repository(db=db)
    local_lm_available = _check_local_lm_available()
    default_lm_url = DEFAULT_LOCAL_URL if local_lm_available else DEFAULT_CLOUD_URL
    lm_base_url = os.getenv("RESUME_MATCHER_LM_BASE_URL", default_lm_url)
    lm_api_key = os.getenv("RESUME_MATCHER_LM_API_KEY", "lm-studio")
    runtime_settings = {
        "lm_base_url": lm_base_url,
        "lm_api_key": lm_api_key,
        "ocr_enabled": True,
        "local_lm_available": local_lm_available,
        "write_mode": False,
        "write_mode_warned": False,
        "write_mode_locked": os.getenv("RESUME_MATCHER_READ_ONLY", "").lower() in ("1", "true", "yes"),
    }
    if os.getenv("RESUME_MATCHER_WRITE_MODE", "").lower() in ("1", "true", "yes"):
        runtime_settings["write_mode"] = True
        runtime_settings["write_mode_locked"] = False

    llm = AIEngine(base_url=runtime_settings["lm_base_url"], api_key=runtime_settings["lm_api_key"])
    analysis = AnalysisService(repo=repo, llm=llm)
    runner = JobRunner(repo=repo, analysis=analysis)
    gh_sync = GitHubSyncService(db_path=settings.db_path)

    @app.on_event("startup")
    def _startup() -> None:
        runner.start()

    @app.on_event("shutdown")
    def _shutdown() -> None:
        runner.stop()

    @app.get("/")
    def console():
        return render_console()

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/v1/jobs", response_model=list[JobOut])
    def list_jobs() -> list[JobOut]:
        return [JobOut(**row) for row in repo.list_jobs()]

    @app.get("/v1/jobs/{job_id}")
    def get_job(job_id: int) -> dict:
        row = repo.get_job(job_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return row

    @app.post("/v1/jobs", response_model=JobOut)
    def ingest_job(payload: JobIn) -> JobOut:
        try:
            row = analysis.ingest_job(
                filename=payload.filename, content=payload.content, tags=payload.tags
            )
            return JobOut(**row)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.put("/v1/jobs/{job_id}")
    def update_job(job_id: int, payload: dict) -> dict:
        try:
            repo.update_job_metadata(
                job_id=job_id,
                criteria=payload.get("criteria"),
                tags=payload.get("tags"),
            )
            return {"ok": True}
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/v1/jobs/{job_id}")
    def delete_job(job_id: int) -> dict:
        try:
            repo.delete_job(job_id)
            return {"ok": True}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/v1/resumes", response_model=list[ResumeOut])
    def list_resumes() -> list[ResumeOut]:
        return [ResumeOut(**row) for row in repo.list_resumes()]

    @app.get("/v1/resumes/{resume_id}")
    def get_resume(resume_id: int) -> dict:
        row = repo.get_resume(resume_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Resume {resume_id} not found")
        return row

    @app.post("/v1/resumes", response_model=ResumeOut)
    def ingest_resume(payload: ResumeIn) -> ResumeOut:
        try:
            row = analysis.ingest_resume(
                filename=payload.filename, content=payload.content, tags=payload.tags
            )
            return ResumeOut(**row)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.put("/v1/resumes/{resume_id}")
    def update_resume(resume_id: int, payload: dict) -> dict:
        try:
            repo.update_resume_metadata(
                resume_id=resume_id,
                profile=payload.get("profile"),
                tags=payload.get("tags"),
            )
            return {"ok": True}
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.delete("/v1/resumes/{resume_id}")
    def delete_resume(resume_id: int) -> dict:
        try:
            repo.delete_resume(resume_id)
            return {"ok": True}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/v1/matches/score", response_model=MatchOut)
    def score_match(payload: ScoreMatchRequest) -> MatchOut:
        try:
            row = analysis.score_match(
                job_id=payload.job_id,
                resume_id=payload.resume_id,
                threshold=payload.threshold,
                auto_deep=payload.auto_deep,
                run_name=payload.run_name,
                force_rerun_pass1=payload.force_rerun_pass1,
                force_rerun_deep=payload.force_rerun_deep,
            )
            return MatchOut(**row)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/v1/matches")
    def list_matches() -> list[dict]:
        return repo.list_matches(limit=200)

    @app.get("/v1/matches/{match_id}")
    def get_match(match_id: int) -> dict:
        row = repo.get_match_summary(match_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
        return row

    @app.post("/v1/runs", response_model=RunOut)
    def create_run(payload: RunRequest) -> RunOut:
        allowed = {"ingest_job", "ingest_job_file", "ingest_resume", "ingest_resume_file", "score_match"}
        if payload.job_type not in allowed:
            raise HTTPException(status_code=400, detail=f"job_type must be one of {sorted(allowed)}")
        run_id = repo.enqueue_run(job_type=payload.job_type, payload=payload.payload)
        row = repo.get_run(run_id)
        if not row:
            raise HTTPException(status_code=500, detail="Failed to enqueue run")
        return RunOut(**row)

    @app.get("/v1/runs", response_model=list[RunOut])
    def list_runs() -> list[RunOut]:
        return [RunOut(**row) for row in repo.list_runs(limit=200)]

    @app.get("/v1/runs/legacy")
    def list_legacy_runs() -> list[dict]:
        return repo.list_legacy_runs(limit=200)

    @app.get("/v1/runs/legacy/{run_id}/results")
    def legacy_run_results(run_id: int) -> list[dict]:
        return repo.list_legacy_run_results(run_id)

    @app.get("/v1/runs/{run_id}", response_model=RunOut)
    def get_run(run_id: int) -> RunOut:
        row = repo.get_run(run_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        return RunOut(**row)

    @app.post("/v1/runs/{run_id}/resume")
    def resume_run(run_id: int) -> dict:
        row = repo.get_run(run_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        status = str(row.get("status") or "")
        if status == "queued":
            return {"ok": True, "message": f"Run {run_id} is already queued.", "run_id": run_id}
        if status == "completed":
            raise HTTPException(status_code=400, detail="Completed run cannot be resumed.")
        if status == "running" and not bool(row.get("is_stuck")):
            raise HTTPException(status_code=409, detail="Run is currently active (not stuck).")
        payload = dict(row.get("payload") or {})
        if str(row.get("job_type") or "") == "score_match":
            checkpoint_idx = int(payload.get("deep_resume_from", 0) or 0)
            checkpoint_details = payload.get("deep_partial_details") or []
            has_checkpoint = checkpoint_idx > 0 or (isinstance(checkpoint_details, list) and len(checkpoint_details) > 0)
            payload["force_rerun_deep"] = bool(
                payload.get("force_rerun_deep", False)
                or payload.get("auto_deep", False)
                or has_checkpoint
            )
            # When checkpoint exists, continue deep scan from saved requirement index.
            if has_checkpoint:
                payload["force_rerun_pass1"] = False
            else:
                payload["force_rerun_pass1"] = True
        ok = repo.requeue_run(run_id=run_id, payload=payload, current_step="resume_requested")
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to requeue run.")
        if str(row.get("job_type") or "") == "score_match":
            resumed_from = int(payload.get("deep_resume_from", 0) or 0)
            if resumed_from > 0:
                repo.add_run_log(
                    run_id,
                    "warn",
                    f"Run resumed from checkpoint at deep requirement {resumed_from + 1} using existing run id.",
                )
            else:
                repo.add_run_log(run_id, "warn", "Run resumed from queue using existing run id.")
        else:
            repo.add_run_log(run_id, "warn", "Run resumed from queue using existing run id.")
        return {"ok": True, "message": f"Run {run_id} requeued.", "run_id": run_id}

    @app.get("/v1/runs/{run_id}/logs", response_model=list[RunLogOut])
    def get_run_logs(run_id: int) -> list[RunLogOut]:
        row = repo.get_run(run_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        return [RunLogOut(**log) for log in repo.list_run_logs(run_id=run_id, limit=500)]

    @app.get("/v1/dashboard")
    def dashboard() -> dict:
        return repo.dashboard_snapshot()

    @app.get("/v1/tags")
    def list_tags() -> list[str]:
        return repo.list_tags()

    @app.post("/v1/tags")
    def add_tag(payload: dict) -> dict:
        name = str(payload.get("name", "")).strip()
        if not name:
            raise HTTPException(status_code=400, detail="name is required")
        repo.add_tag(name)
        return {"ok": True}

    @app.put("/v1/tags/rename")
    def rename_tag(payload: dict) -> dict:
        old = str(payload.get("old", "")).strip()
        new = str(payload.get("new", "")).strip()
        if not old or not new:
            raise HTTPException(status_code=400, detail="old and new are required")
        repo.rename_tag(old, new)
        return {"ok": True}

    @app.delete("/v1/tags/{name}")
    def delete_tag(name: str) -> dict:
        repo.delete_tag(name)
        return {"ok": True}

    @app.get("/v1/settings/state")
    def get_settings_state() -> dict:
        writer_cfg = gh_sync.writer_config()
        lock_timeout = int(writer_cfg.get("lock_timeout_hours", 6) or 6)
        lock_info = gh_sync.get_lock(timeout_hours=lock_timeout)
        writer_users = [str(u.get("name") or "").strip() for u in (writer_cfg.get("users") or []) if str(u.get("name") or "").strip()]
        return {
            "lm_base_url": runtime_settings["lm_base_url"],
            "lm_api_key": runtime_settings["lm_api_key"],
            "ocr_enabled": bool(runtime_settings["ocr_enabled"]),
            "local_lm_available": bool(runtime_settings["local_lm_available"]),
            "write_mode": bool(runtime_settings["write_mode"]),
            "write_mode_locked": bool(runtime_settings["write_mode_locked"]),
            "writer_default_name": writer_cfg.get("default_name", ""),
            "writer_users": writer_users,
            "lock_timeout_hours": lock_timeout,
            "lock_info": lock_info,
            "github_configured": bool(gh_sync._credentials()[0] and gh_sync._credentials()[1]),
        }

    def _resolve_writer_identity(payload: dict, require_password: bool = True) -> tuple[str, str]:
        writer_cfg = gh_sync.writer_config()
        writer_name = str(payload.get("writer_name") or writer_cfg.get("default_name") or "unknown").strip()
        writer_password = str(payload.get("writer_password") or "")
        users = writer_cfg.get("users") or []

        if users:
            match = None
            for row in users:
                name = str((row or {}).get("name") or "").strip()
                if name.lower() == writer_name.lower():
                    match = row
                    writer_name = name
                    break
            if not match:
                raise HTTPException(status_code=401, detail="Writer is not authorized for write mode.")
            expected = str(match.get("password") or "")
            if require_password and writer_password != expected:
                raise HTTPException(status_code=401, detail="Incorrect write password.")
            return writer_name, writer_password

        expected = str(writer_cfg.get("password") or "").strip()
        if require_password:
            if not expected:
                raise HTTPException(status_code=400, detail="Write password is not configured in secrets.")
            if writer_password != expected:
                raise HTTPException(status_code=401, detail="Incorrect write password.")
        return writer_name, writer_password

    @app.put("/v1/settings/runtime")
    def update_runtime_settings(payload: dict) -> dict:
        if "lm_base_url" in payload:
            runtime_settings["lm_base_url"] = str(payload.get("lm_base_url", "")).strip() or runtime_settings["lm_base_url"]
        if "lm_api_key" in payload:
            runtime_settings["lm_api_key"] = str(payload.get("lm_api_key", "")).strip() or runtime_settings["lm_api_key"]
        if "ocr_enabled" in payload:
            runtime_settings["ocr_enabled"] = bool(payload.get("ocr_enabled"))
        analysis.llm = AIEngine(
            base_url=runtime_settings["lm_base_url"],
            api_key=runtime_settings["lm_api_key"],
        )
        return {"ok": True}

    @app.post("/v1/settings/test-connection")
    def test_connection(payload: dict | None = None) -> dict:
        p = payload or {}
        url = str(p.get("lm_base_url") or runtime_settings["lm_base_url"])
        key = str(p.get("lm_api_key") or runtime_settings["lm_api_key"])
        try:
            client = OpenAI(base_url=url, api_key=key)
            models = client.models.list()
            count = len(getattr(models, "data", []) or [])
            return {"ok": True, "message": f"Connected to LM Studio. Found {count} model(s)."}
        except Exception as exc:
            return {"ok": False, "message": f"Connection failed: {exc}"}

    @app.post("/v1/settings/write-mode/enable")
    def enable_write_mode(payload: dict) -> dict:
        if runtime_settings["write_mode_locked"]:
            raise HTTPException(status_code=403, detail="Write mode is locked by launcher/env.")
        writer_cfg = gh_sync.writer_config()
        writer_name, _ = _resolve_writer_identity(payload, require_password=True)
        timeout_hours = int(writer_cfg.get("lock_timeout_hours", 6) or 6)
        lock = gh_sync.get_lock(timeout_hours=timeout_hours)
        if lock and isinstance(lock, dict) and lock.get("owner") == (writer_name or "unknown"):
            runtime_settings["write_mode"] = True
            runtime_settings["write_mode_warned"] = False
            return {"ok": True, "message": "Write mode resumed (existing lock)."}
        ok, msg = gh_sync.acquire_lock(writer_name or "unknown", timeout_hours=timeout_hours)
        if not ok:
            raise HTTPException(status_code=409, detail=msg)
        runtime_settings["write_mode"] = True
        runtime_settings["write_mode_warned"] = False
        return {"ok": True, "message": msg}

    @app.post("/v1/settings/write-mode/disable")
    def disable_write_mode(payload: dict) -> dict:
        writer_name, _ = _resolve_writer_identity(payload, require_password=True)
        ok, msg = gh_sync.release_lock(writer_name or "unknown")
        if not ok:
            raise HTTPException(status_code=409, detail=msg)
        runtime_settings["write_mode"] = False
        runtime_settings["write_mode_warned"] = False
        return {"ok": True, "message": msg}

    @app.post("/v1/settings/write-mode/force-unlock")
    def force_unlock_write_mode(payload: dict) -> dict:
        writer_name, _ = _resolve_writer_identity(payload, require_password=True)
        ok, msg = gh_sync.release_lock(writer_name or "unknown", force=True)
        if not ok:
            raise HTTPException(status_code=409, detail=msg)
        runtime_settings["write_mode"] = False
        runtime_settings["write_mode_warned"] = False
        return {"ok": True, "message": msg}

    @app.post("/v1/settings/sync/push")
    def push_db() -> dict:
        if not runtime_settings["write_mode"]:
            raise HTTPException(status_code=403, detail="Read-only mode: enable Write Mode to push.")
        ok, msg = gh_sync.push_db()
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"ok": True, "message": msg}

    @app.post("/v1/settings/sync/pull")
    def pull_db() -> dict:
        ok, msg = gh_sync.pull_db()
        if not ok:
            raise HTTPException(status_code=400, detail=msg)
        return {"ok": True, "message": msg}

    @app.post("/v1/settings/reset-db")
    def reset_db() -> dict:
        repo.reset_all_data()
        if runtime_settings["write_mode"]:
            gh_sync.push_db()
        return {"ok": True, "message": "Database reset complete."}

    return app


app = create_app()
