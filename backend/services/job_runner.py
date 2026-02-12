import threading
import time
import traceback
import json
import base64
import os
from dataclasses import dataclass, field
from typing import Callable

import document_utils

from .analysis import AnalysisService
from .repository import Repository


@dataclass
class JobRunner:
    repo: Repository
    analysis: AnalysisService
    poll_seconds: float = 0.6
    on_run_terminal: Callable[[int, str], None] | None = None
    _stop_event: threading.Event = field(default_factory=threading.Event)
    _thread: threading.Thread | None = None
    _heartbeat_interval_sec: float = field(
        default_factory=lambda: max(5.0, float(os.getenv("RESUME_MATCHER_RUN_HEARTBEAT_SEC", "20") or 20.0))
    )

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="job-runner", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                run = self.repo.claim_next_run()
                if not run:
                    time.sleep(self.poll_seconds)
                    continue
                run_id = int(run["id"])
                self.repo.add_run_log(run_id, "info", f"Run picked up: {run['job_type']}")
                heartbeat_stop = threading.Event()
                heartbeat_thread = threading.Thread(
                    target=self._run_heartbeat_loop,
                    name=f"run-heartbeat-{run_id}",
                    args=(run_id, heartbeat_stop),
                    daemon=True,
                )
                heartbeat_thread.start()
                try:
                    result = self._execute(run_id=run_id, job_type=run["job_type"], payload=run.get("payload") or {})
                    self.repo.complete_run(run_id=run_id, result=result)
                    self.repo.add_run_log(run_id, "info", "Run completed")
                    if self.on_run_terminal:
                        try:
                            self.on_run_terminal(run_id, "completed")
                        except Exception:
                            print(f"[job-runner] on_run_terminal(completed) failed for run {run_id}")
                except Exception as exc:
                    self.repo.fail_run(run_id=run_id, error=str(exc))
                    self.repo.add_run_log(run_id, "error", f"{exc}\n{traceback.format_exc()}")
                    if self.on_run_terminal:
                        try:
                            self.on_run_terminal(run_id, "failed")
                        except Exception:
                            print(f"[job-runner] on_run_terminal(failed) failed for run {run_id}")
                finally:
                    heartbeat_stop.set()
                    heartbeat_thread.join(timeout=1.0)
            except Exception:
                # Keep the worker alive if queue polling fails transiently.
                print("[job-runner] loop error:\n" + traceback.format_exc())
                time.sleep(self.poll_seconds)

    def _run_heartbeat_loop(self, run_id: int, stop_event: threading.Event) -> None:
        while not stop_event.wait(self._heartbeat_interval_sec):
            try:
                row = self.repo.get_run(run_id)
                if not row:
                    return
                if str(row.get("status") or "") != "running":
                    return
                step = str(row.get("current_step") or "-")
                progress = int(row.get("progress") or 0)
                self.repo.add_run_log(
                    run_id,
                    "debug",
                    f"Heartbeat: run active at {progress}% (step={step}). Waiting on LLM/IO if no new requirement log yet.",
                )
            except Exception:
                # Heartbeat should never interrupt the worker.
                return

    def _execute(self, run_id: int, job_type: str, payload: dict) -> dict:
        if job_type == "ingest_job":
            self.repo.update_run_progress(run_id, 10, "analyzing job description")
            self.repo.add_run_log(run_id, "info", "Analyzing JD")
            row = self.analysis.ingest_job(
                filename=str(payload.get("filename", "")),
                content=str(payload.get("content", "")),
                tags=list(payload.get("tags", [])),
            )
            self.repo.update_run_progress(run_id, 100, "job ingested")
            return {"job_id": row["id"], "filename": row["filename"]}

        if job_type == "ingest_job_file":
            self.repo.update_run_progress(run_id, 10, "extracting file")
            filename = str(payload.get("filename", ""))
            content_b64 = str(payload.get("content_b64", "") or "")
            tags = list(payload.get("tags", []))
            force_reparse = bool(payload.get("force_reparse", False))
            if not filename or not content_b64:
                raise ValueError("filename and content_b64 are required for ingest_job_file")

            existing = self.repo.db.get_job_by_filename(filename)
            if existing and not force_reparse:
                self.repo.add_run_log(run_id, "info", f"Skipped existing JD '{filename}' (force_reparse disabled).")
                self.repo.update_run_progress(run_id, 100, "skipped existing")
                return {"job_id": int(existing["id"]), "filename": filename, "skipped": True}

            raw_bytes = base64.b64decode(content_b64.encode("utf-8"))
            lower = filename.lower()
            if lower.endswith(".pdf"):
                text = document_utils.extract_text_from_pdf(raw_bytes, use_ocr=True)
            elif lower.endswith(".docx"):
                text = document_utils.extract_text_from_docx(raw_bytes)
            else:
                text = raw_bytes.decode("utf-8", errors="ignore")

            self.repo.update_run_progress(run_id, 60, "analyzing job description")
            criteria = self.analysis.llm.analyze_jd(text)
            if not isinstance(criteria, dict) or criteria.get("error"):
                raise RuntimeError(f"JD analysis failed for '{filename}': {criteria}")

            if existing:
                job_id = int(existing["id"])
                self.repo.db.update_job_content(job_id, text, criteria)
                if tags:
                    self.repo.db.update_job_tags(job_id, ",".join([t for t in tags if str(t).strip()]))
                for t in tags:
                    if str(t).strip():
                        self.repo.add_tag(str(t).strip())
                row = self.repo.get_job(job_id)
            else:
                row = self.repo.add_job(filename=filename, content=text, criteria=criteria, tags=tags)
                for t in tags:
                    if str(t).strip():
                        self.repo.add_tag(str(t).strip())

            self.repo.update_run_progress(run_id, 100, "job ingested")
            return {"job_id": row["id"], "filename": row["filename"]}

        if job_type == "ingest_resume":
            self.repo.update_run_progress(run_id, 10, "analyzing resume")
            self.repo.add_run_log(run_id, "info", "Analyzing resume")
            profile_override = payload.get("profile")
            if profile_override is not None:
                self.repo.add_run_log(run_id, "info", "Using provided profile payload from import.")
                profile_payload = profile_override
                if isinstance(profile_payload, str):
                    try:
                        profile_payload = json.loads(profile_payload)
                    except Exception:
                        profile_payload = {}
                if not isinstance(profile_payload, dict):
                    profile_payload = {}
                row = self.repo.add_resume(
                    filename=str(payload.get("filename", "")),
                    content=str(payload.get("content", "")),
                    profile=profile_payload,
                    tags=list(payload.get("tags", [])),
                )
            else:
                row = self.analysis.ingest_resume(
                    filename=str(payload.get("filename", "")),
                    content=str(payload.get("content", "")),
                    tags=list(payload.get("tags", [])),
                )
            self.repo.update_run_progress(run_id, 100, "resume ingested")
            return {"resume_id": row["id"], "filename": row["filename"]}

        if job_type == "ingest_resume_file":
            self.repo.update_run_progress(run_id, 10, "extracting file")
            filename = str(payload.get("filename", ""))
            content_b64 = str(payload.get("content_b64", "") or "")
            tags = list(payload.get("tags", []))
            force_reparse = bool(payload.get("force_reparse", False))
            if not filename or not content_b64:
                raise ValueError("filename and content_b64 are required for ingest_resume_file")

            existing = self.repo.db.get_resume_by_filename(filename)
            if existing and not force_reparse:
                self.repo.add_run_log(run_id, "info", f"Skipped existing resume '{filename}' (force_reparse disabled).")
                self.repo.update_run_progress(run_id, 100, "skipped existing")
                return {"resume_id": int(existing["id"]), "filename": filename, "skipped": True}

            raw_bytes = base64.b64decode(content_b64.encode("utf-8"))
            lower = filename.lower()
            if lower.endswith(".pdf"):
                text = document_utils.extract_text_from_pdf(raw_bytes, use_ocr=True)
            elif lower.endswith(".docx"):
                text = document_utils.extract_text_from_docx(raw_bytes)
            else:
                text = raw_bytes.decode("utf-8", errors="ignore")

            self.repo.update_run_progress(run_id, 60, "analyzing resume")
            profile = self.analysis.llm.analyze_resume(text)
            if not isinstance(profile, dict):
                raise RuntimeError(f"Resume analysis failed for '{filename}'.")

            if existing:
                resume_id = int(existing["id"])
                self.repo.db.update_resume_content(resume_id, text, profile)
                if tags:
                    self.repo.db.update_resume_tags(resume_id, ",".join([t for t in tags if str(t).strip()]))
                for t in tags:
                    if str(t).strip():
                        self.repo.add_tag(str(t).strip())
                row = self.repo.get_resume(resume_id)
            else:
                row = self.repo.add_resume(filename=filename, content=text, profile=profile, tags=tags)
                for t in tags:
                    if str(t).strip():
                        self.repo.add_tag(str(t).strip())

            self.repo.update_run_progress(run_id, 100, "resume ingested")
            return {"resume_id": row["id"], "filename": row["filename"]}

        if job_type == "score_match":
            self.repo.update_run_progress(run_id, 10, "scoring")
            job_id = int(payload["job_id"])
            resume_id = int(payload["resume_id"])
            threshold = int(payload.get("threshold", 50))
            auto_deep = bool(payload.get("auto_deep", False))
            force_rerun_pass1 = bool(payload.get("force_rerun_pass1", False))
            force_rerun_deep = bool(payload.get("force_rerun_deep", False))
            deep_resume_from = int(payload.get("deep_resume_from", 0) or 0)
            deep_partial_details = payload.get("deep_partial_details") or []

            self.repo.add_run_log(
                run_id,
                "info",
                (
                    "Scoring match "
                    f"(job_id={job_id}, resume_id={resume_id}, threshold={threshold}, "
                    f"auto_deep={auto_deep}, force_pass1={force_rerun_pass1}, force_deep={force_rerun_deep})"
                ),
            )
            job = self.repo.get_job(job_id)
            resume = self.repo.get_resume(resume_id)
            job_name = (job or {}).get("filename") or f"job:{job_id}"
            resume_name = (resume or {}).get("filename") or f"resume:{resume_id}"
            self.repo.add_run_log(
                run_id,
                "info",
                f"Context: JD='{job_name}' vs Resume='{resume_name}'",
            )

            existing_before = self.repo.get_existing_match(job_id, resume_id)
            predicted_reuse = False
            force_any = bool(force_rerun_pass1 or force_rerun_deep)
            wants_deep = bool(auto_deep or force_rerun_deep)
            if existing_before and not force_any:
                existing_strategy = str(existing_before.get("strategy") or "Standard")
                if (not wants_deep) or (wants_deep and existing_strategy == "Deep"):
                    predicted_reuse = True
            if predicted_reuse and existing_before:
                self.repo.add_run_log(
                    run_id,
                    "info",
                    (
                        "Cache check: existing match can be reused "
                        f"(id={existing_before.get('id')}, strategy={existing_before.get('strategy')}, "
                        f"score={existing_before.get('match_score')}%, decision={existing_before.get('decision')})"
                    ),
                )
            elif existing_before:
                self.repo.add_run_log(
                    run_id,
                    "info",
                    "Cache check: existing match found but recomputation forced by current options.",
                )
            else:
                self.repo.add_run_log(run_id, "info", "Cache check: no existing match found.")

            row = self.analysis.score_match(
                job_id=job_id,
                resume_id=resume_id,
                threshold=threshold,
                auto_deep=auto_deep,
                run_name=payload.get("run_name"),
                force_rerun_pass1=force_rerun_pass1,
                force_rerun_deep=force_rerun_deep,
                log_fn=lambda msg: self.repo.add_run_log(run_id, "info", str(msg)),
                deep_resume_from=deep_resume_from,
                deep_partial_details=deep_partial_details if isinstance(deep_partial_details, list) else [],
                progress_fn=lambda idx, total, details: self._checkpoint_deep_progress(
                    run_id=run_id,
                    payload=payload,
                    idx=idx,
                    total=total,
                    details=details,
                ),
            )
            if predicted_reuse and existing_before and int(row["id"]) == int(existing_before["id"]):
                self.repo.add_run_log(
                    run_id,
                    "info",
                    (
                        f"Reused existing match id={row['id']} "
                        f"(strategy={row.get('strategy')}, score={row.get('match_score')}%, decision={row.get('decision')})"
                    ),
                )
            else:
                self.repo.add_run_log(
                    run_id,
                    "info",
                    (
                        f"Saved match id={row['id']} "
                        f"(strategy={row.get('strategy')}, score={row.get('match_score')}%, decision={row.get('decision')})"
                    ),
                )
            self.repo.update_run_progress(run_id, 100, "match scored")
            return {"match_id": row["id"], "score": row["match_score"], "decision": row["decision"]}

        raise ValueError(f"Unsupported job_type: {job_type}")

    def _checkpoint_deep_progress(self, run_id: int, payload: dict, idx: int, total: int, details: list) -> None:
        payload["deep_resume_from"] = int(idx)
        payload["deep_partial_details"] = list(details or [])
        pct = 10 + int((max(0, min(idx, total)) / max(1, total)) * 85)
        self.repo.update_run_payload(run_id=run_id, payload=payload)
        self.repo.update_run_result(run_id=run_id, result={"deep_partial_details": payload["deep_partial_details"]})
        self.repo.update_run_progress(run_id=run_id, progress=min(95, pct), current_step=f"deep_scan_{idx}_of_{total}")
