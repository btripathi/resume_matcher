import threading
import time
import traceback
import json
import base64
import os
import re
from dataclasses import dataclass, field
from typing import Callable

import document_utils

from .analysis import AnalysisService
from .repository import Repository


class RunCanceledError(RuntimeError):
    pass


class RunPausedError(RuntimeError):
    pass


@dataclass
class JobRunner:
    repo: Repository
    analysis: AnalysisService
    poll_seconds: float = 0.6
    on_run_terminal: Callable[[int, str], None] | None = None
    can_pick_next_run: Callable[[], bool] | None = None
    max_running_getter: Callable[[], int] | int = 1
    worker_pool_size: int = field(
        default_factory=lambda: max(1, int(os.getenv("RESUME_MATCHER_JOB_WORKER_POOL", "16") or 16))
    )
    _stop_event: threading.Event = field(default_factory=threading.Event)
    _threads: list[threading.Thread] = field(default_factory=list)
    _heartbeat_interval_sec: float = field(
        default_factory=lambda: max(5.0, float(os.getenv("RESUME_MATCHER_RUN_HEARTBEAT_SEC", "20") or 20.0))
    )

    def start(self) -> None:
        if any(t.is_alive() for t in self._threads):
            return
        self._stop_event.clear()
        self._threads = []
        workers = max(1, int(self.worker_pool_size or 1))
        for i in range(workers):
            t = threading.Thread(target=self._run_loop, name=f"job-runner-{i+1}", daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self) -> None:
        self._stop_event.set()
        for t in self._threads:
            t.join(timeout=2.0)
        self._threads = []

    def _max_running(self) -> int:
        src = self.max_running_getter
        try:
            value = int(src() if callable(src) else src)
        except Exception:
            value = 1
        return max(1, value)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                if self.can_pick_next_run and not self.can_pick_next_run():
                    time.sleep(self.poll_seconds)
                    continue
                run = self.repo.claim_next_run(max_running=self._max_running())
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
                    if self.repo.is_run_canceled(run_id):
                        self.repo.add_run_log(run_id, "warn", "Run execution finished after cancellation; preserving canceled state.")
                        if self.on_run_terminal:
                            try:
                                self.on_run_terminal(run_id, "canceled")
                            except Exception:
                                print(f"[job-runner] on_run_terminal(canceled) failed for run {run_id}")
                    else:
                        self.repo.complete_run(run_id=run_id, result=result)
                        self.repo.add_run_log(run_id, "info", "Run completed")
                        if self.on_run_terminal:
                            try:
                                self.on_run_terminal(run_id, "completed")
                            except Exception:
                                print(f"[job-runner] on_run_terminal(completed) failed for run {run_id}")
                except RunCanceledError:
                    self.repo.add_run_log(run_id, "warn", "Run canceled by user request.")
                    if self.on_run_terminal:
                        try:
                            self.on_run_terminal(run_id, "canceled")
                        except Exception:
                            print(f"[job-runner] on_run_terminal(canceled) failed for run {run_id}")
                except RunPausedError as exc:
                    reason = str(exc or "paused")
                    self.repo.mark_run_paused(run_id=run_id, reason=reason)
                    self.repo.add_run_log(run_id, "warn", f"Run paused by user request: {reason}")
                    if self.on_run_terminal:
                        try:
                            self.on_run_terminal(run_id, "paused")
                        except Exception:
                            print(f"[job-runner] on_run_terminal(paused) failed for run {run_id}")
                except Exception as exc:
                    if self.repo.is_run_canceled(run_id):
                        self.repo.add_run_log(run_id, "warn", "Run canceled while in progress; failure details suppressed.")
                        if self.on_run_terminal:
                            try:
                                self.on_run_terminal(run_id, "canceled")
                            except Exception:
                                print(f"[job-runner] on_run_terminal(canceled) failed for run {run_id}")
                    else:
                        pause_requested, pause_reason = self.repo.is_run_pause_requested(run_id)
                        if pause_requested:
                            self.repo.mark_run_paused(run_id=run_id, reason=pause_reason)
                            self.repo.add_run_log(run_id, "warn", f"Run paused while in progress: {pause_reason}")
                            if self.on_run_terminal:
                                try:
                                    self.on_run_terminal(run_id, "paused")
                                except Exception:
                                    print(f"[job-runner] on_run_terminal(paused) failed for run {run_id}")
                            continue
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
                payload = row.get("payload") or {}
                pause_requested = bool(payload.get("pause_requested")) if isinstance(payload, dict) else False
                if pause_requested or step == "pause_requested":
                    self.repo.add_run_log(
                        run_id,
                        "debug",
                        f"Heartbeat: pause requested at {progress}% (step={step}). Waiting for current LLM/IO step to return before pausing.",
                    )
                    continue
                self.repo.add_run_log(
                    run_id,
                    "debug",
                    f"Heartbeat: run active at {progress}% (step={step}). Waiting on LLM/IO if no new requirement log yet.",
                )
            except Exception:
                # Heartbeat should never interrupt the worker.
                return

    def _ensure_not_canceled(self, run_id: int) -> None:
        if self.repo.is_run_canceled(run_id):
            raise RunCanceledError(f"Run {run_id} canceled.")
        pause_requested, pause_reason = self.repo.is_run_pause_requested(run_id)
        if pause_requested:
            raise RunPausedError(pause_reason or "paused")

    def _extract_uploaded_text(self, filename: str, content_b64: str) -> str:
        raw_bytes = base64.b64decode(content_b64.encode("utf-8"))
        lower = filename.lower()
        if lower.endswith(".pdf"):
            return document_utils.extract_text_from_pdf(raw_bytes, use_ocr=True)
        if lower.endswith(".docx"):
            return document_utils.extract_text_from_docx(raw_bytes)
        return raw_bytes.decode("utf-8", errors="ignore")

    def _normalize_extracted_text(self, text: str) -> str:
        raw = str(text or "")
        if not raw:
            return ""
        raw = raw.replace("\r\n", "\n").replace("\r", "\n")
        raw = raw.replace("\u00a0", " ")

        def collapse_single_char_runs(segment: str) -> str:
            tokens = segment.split()
            if not tokens:
                return ""
            out: list[str] = []
            i = 0
            while i < len(tokens):
                tok = tokens[i]
                if len(tok) == 1 and tok.isalnum():
                    run: list[str] = [tok]
                    j = i + 1
                    while j < len(tokens) and len(tokens[j]) == 1 and tokens[j].isalnum():
                        run.append(tokens[j])
                        j += 1
                    if len(run) >= 2:
                        out.append("".join(run))
                        i = j
                        continue
                out.append(tok)
                i += 1
            return " ".join(out)

        def looks_ocr_spaced(line: str) -> bool:
            tokens = [t for t in line.split() if t]
            if len(tokens) < 6:
                return False
            single_count = sum(1 for t in tokens if len(t) == 1)
            alpha_single_count = sum(1 for t in tokens if len(t) == 1 and t.isalpha())
            return single_count / max(len(tokens), 1) >= 0.6 and alpha_single_count >= 4

        def normalize_line(line: str) -> str:
            stripped = line.strip()
            if not stripped:
                return ""
            if looks_ocr_spaced(stripped):
                # Multi-space gaps are usually real word boundaries in OCR letter-spaced lines.
                parts = [collapse_single_char_runs(p) for p in re.split(r"\s{2,}", stripped) if p.strip()]
                merged = " ".join(parts)
            else:
                merged = re.sub(r"\s{2,}", " ", stripped)
            merged = re.sub(r"\s+([,.;:!?])", r"\1", merged)
            merged = re.sub(r"([(\[])\s+", r"\1", merged)
            merged = re.sub(r"\s+([)\]])", r"\1", merged)
            merged = re.sub(r"\s*\|\s*", " | ", merged)
            merged = re.sub(r"\s{2,}", " ", merged).strip()
            return merged

        lines = [normalize_line(line) for line in raw.split("\n")]
        out_lines: list[str] = []
        blank_streak = 0
        for ln in lines:
            if ln:
                blank_streak = 0
                out_lines.append(ln)
            else:
                blank_streak += 1
                if blank_streak <= 1:
                    out_lines.append("")
        return "\n".join(out_lines).strip()

    def _infer_document_type(self, filename: str, text: str) -> tuple[str, int, int]:
        name = str(filename or "").lower()
        sample = str(text or "")[:12000].lower()

        jd_name_patterns = [r"\bjd\b", r"job[ _-]?description", r"\brole\b", r"\bopening\b", r"\bhiring\b"]
        resume_name_patterns = [r"\bresume\b", r"\bcv\b", r"\bprofile\b", r"naukri", r"candidate"]
        jd_text_patterns = [
            r"\bresponsibilit(y|ies)\b",
            r"\bqualifications?\b",
            r"\brequirements?\b",
            r"\bmust[- ]?have\b",
            r"\bnice[- ]?to[- ]?have\b",
            r"\babout (the )?role\b",
            r"\bwe are looking for\b",
            r"\bjob description\b",
        ]
        resume_text_patterns = [
            r"\bwork experience\b",
            r"\bprofessional summary\b",
            r"\beducation\b",
            r"\bskills?\b",
            r"\bprojects?\b",
            r"\bcertifications?\b",
            r"\bphone\b",
            r"\bemail\b",
            r"\blinkedin\b",
        ]

        jd_score = sum(2 for p in jd_name_patterns if re.search(p, name))
        resume_score = sum(2 for p in resume_name_patterns if re.search(p, name))
        jd_score += sum(1 for p in jd_text_patterns if re.search(p, sample))
        resume_score += sum(1 for p in resume_text_patterns if re.search(p, sample))

        kind = "job" if jd_score >= resume_score else "resume"
        return kind, jd_score, resume_score

    def _execute(self, run_id: int, job_type: str, payload: dict) -> dict:
        self._ensure_not_canceled(run_id)
        if job_type == "ingest_job":
            self.repo.update_run_progress(run_id, 10, "analyzing job description")
            self.repo.add_run_log(run_id, "info", "Analyzing JD")
            self._ensure_not_canceled(run_id)
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

            self._ensure_not_canceled(run_id)
            text = self._normalize_extracted_text(self._extract_uploaded_text(filename=filename, content_b64=content_b64))

            self.repo.update_run_progress(run_id, 60, "analyzing job description")
            self._ensure_not_canceled(run_id)
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
            self._ensure_not_canceled(run_id)
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

            self._ensure_not_canceled(run_id)
            text = self._normalize_extracted_text(self._extract_uploaded_text(filename=filename, content_b64=content_b64))

            self.repo.update_run_progress(run_id, 60, "analyzing resume")
            self._ensure_not_canceled(run_id)
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

        if job_type == "ingest_auto_file":
            self.repo.update_run_progress(run_id, 10, "extracting file")
            filename = str(payload.get("filename", ""))
            content_b64 = str(payload.get("content_b64", "") or "")
            tags = list(payload.get("tags", []))
            force_reparse = bool(payload.get("force_reparse", False))
            if not filename or not content_b64:
                raise ValueError("filename and content_b64 are required for ingest_auto_file")

            self._ensure_not_canceled(run_id)
            text = self._normalize_extracted_text(self._extract_uploaded_text(filename=filename, content_b64=content_b64))
            self.repo.update_run_progress(run_id, 35, "classifying document type")
            kind, jd_score, resume_score = self._infer_document_type(filename=filename, text=text)
            self.repo.add_run_log(
                run_id,
                "info",
                f"Auto-classified '{filename}' as {kind.upper()} (jd_score={jd_score}, resume_score={resume_score}).",
            )
            self._ensure_not_canceled(run_id)

            if kind == "job":
                existing = self.repo.db.get_job_by_filename(filename)
                if existing and not force_reparse:
                    self.repo.add_run_log(run_id, "info", f"Skipped existing JD '{filename}' (force_reparse disabled).")
                    self.repo.update_run_progress(run_id, 100, "skipped existing")
                    return {"document_type": "job", "job_id": int(existing["id"]), "filename": filename, "skipped": True}

                self.repo.update_run_progress(run_id, 60, "analyzing job description")
                self._ensure_not_canceled(run_id)
                criteria = self.analysis.llm.analyze_jd(text)
                if not isinstance(criteria, dict) or criteria.get("error"):
                    raise RuntimeError(f"JD analysis failed for '{filename}': {criteria}")
                if existing:
                    job_id = int(existing["id"])
                    self.repo.db.update_job_content(job_id, text, criteria)
                    if tags:
                        self.repo.db.update_job_tags(job_id, ",".join([t for t in tags if str(t).strip()]))
                    row = self.repo.get_job(job_id)
                else:
                    row = self.repo.add_job(filename=filename, content=text, criteria=criteria, tags=tags)
                for t in tags:
                    if str(t).strip():
                        self.repo.add_tag(str(t).strip())
                self.repo.update_run_progress(run_id, 100, "job ingested")
                return {"document_type": "job", "job_id": row["id"], "filename": row["filename"]}

            existing = self.repo.db.get_resume_by_filename(filename)
            if existing and not force_reparse:
                self.repo.add_run_log(run_id, "info", f"Skipped existing resume '{filename}' (force_reparse disabled).")
                self.repo.update_run_progress(run_id, 100, "skipped existing")
                return {"document_type": "resume", "resume_id": int(existing["id"]), "filename": filename, "skipped": True}

            self.repo.update_run_progress(run_id, 60, "analyzing resume")
            self._ensure_not_canceled(run_id)
            profile = self.analysis.llm.analyze_resume(text)
            if not isinstance(profile, dict):
                raise RuntimeError(f"Resume analysis failed for '{filename}'.")
            if existing:
                resume_id = int(existing["id"])
                self.repo.db.update_resume_content(resume_id, text, profile)
                if tags:
                    self.repo.db.update_resume_tags(resume_id, ",".join([t for t in tags if str(t).strip()]))
                row = self.repo.get_resume(resume_id)
            else:
                row = self.repo.add_resume(filename=filename, content=text, profile=profile, tags=tags)
            for t in tags:
                if str(t).strip():
                    self.repo.add_tag(str(t).strip())
            self.repo.update_run_progress(run_id, 100, "resume ingested")
            return {"document_type": "resume", "resume_id": row["id"], "filename": row["filename"]}

        if job_type == "reprocess_job":
            self.repo.update_run_progress(run_id, 10, "loading existing job")
            job_id = int(payload.get("job_id", 0) or 0)
            if not job_id:
                raise ValueError("job_id is required for reprocess_job")
            existing = self.repo.get_job(job_id)
            if not existing:
                raise ValueError(f"Job {job_id} not found")
            self._ensure_not_canceled(run_id)
            normalized_text = self._normalize_extracted_text(str(existing.get("content") or ""))
            self.repo.update_run_progress(run_id, 60, "reanalyzing job description")
            self._ensure_not_canceled(run_id)
            criteria = self.analysis.llm.analyze_jd(normalized_text)
            if not isinstance(criteria, dict) or criteria.get("error"):
                raise RuntimeError(f"JD analysis failed for '{existing.get('filename', '')}': {criteria}")
            self.repo.db.update_job_content(job_id, normalized_text, criteria)
            self.repo.update_run_progress(run_id, 100, "job reprocessed")
            return {
                "document_type": "job",
                "job_id": job_id,
                "filename": existing.get("filename"),
                "normalized": True,
            }

        if job_type == "reprocess_resume":
            self.repo.update_run_progress(run_id, 10, "loading existing resume")
            resume_id = int(payload.get("resume_id", 0) or 0)
            if not resume_id:
                raise ValueError("resume_id is required for reprocess_resume")
            existing = self.repo.get_resume(resume_id)
            if not existing:
                raise ValueError(f"Resume {resume_id} not found")
            self._ensure_not_canceled(run_id)
            normalized_text = self._normalize_extracted_text(str(existing.get("content") or ""))
            self.repo.update_run_progress(run_id, 60, "reanalyzing resume")
            self._ensure_not_canceled(run_id)
            profile = self.analysis.llm.analyze_resume(normalized_text)
            if not isinstance(profile, dict):
                raise RuntimeError(f"Resume analysis failed for '{existing.get('filename', '')}'.")
            self.repo.db.update_resume_content(resume_id, normalized_text, profile)
            self.repo.update_run_progress(run_id, 100, "resume reprocessed")
            return {
                "document_type": "resume",
                "resume_id": resume_id,
                "filename": existing.get("filename"),
                "normalized": True,
            }

        if job_type == "score_match":
            self.repo.update_run_progress(run_id, 10, "scoring")
            self._ensure_not_canceled(run_id)
            job_id = int(payload["job_id"])
            resume_id = int(payload["resume_id"])
            threshold = int(payload.get("threshold", 50))
            auto_deep = bool(payload.get("auto_deep", False))
            legacy_run_id = int(payload.get("legacy_run_id", 0) or 0) or None
            force_rerun_pass1 = bool(payload.get("force_rerun_pass1", False))
            force_rerun_deep = bool(payload.get("force_rerun_deep", False))
            deep_single_prompt = bool(payload.get("deep_single_prompt", False))
            debug_bulk_log = bool(payload.get("debug_bulk_log", False))
            max_deep_scans_per_jd = int(payload.get("max_deep_scans_per_jd", 0) or 0)
            ai_concurrency = max(1, int(payload.get("ai_concurrency", 1) or 1))
            deep_resume_from = int(payload.get("deep_resume_from", 0) or 0)
            deep_partial_details = payload.get("deep_partial_details") or []

            self.repo.add_run_log(
                run_id,
                "info",
                (
                    "Scoring match "
                    f"(job_id={job_id}, resume_id={resume_id}, threshold={threshold}, "
                    f"auto_deep={auto_deep}, force_pass1={force_rerun_pass1}, force_deep={force_rerun_deep}, "
                    f"deep_single_prompt={deep_single_prompt}, debug_bulk_log={debug_bulk_log}, "
                    f"max_deep_per_jd={max_deep_scans_per_jd}, ai_concurrency={ai_concurrency})"
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
            existing_strategy = str((existing_before or {}).get("strategy") or "Standard")
            if existing_before and not force_any:
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
                    (
                        "Cache check: existing match found but recomputation required "
                        f"(existing strategy={existing_strategy}; "
                        + (
                            "reason=force_rerun_pass1/force_rerun_deep enabled"
                            if force_any
                            else ("reason=deep output requested and cached result is not Deep" if wants_deep else "reason=options changed")
                        )
                        + ")."
                    ),
                )
            else:
                self.repo.add_run_log(run_id, "info", "Cache check: no existing match found.")

            row = self.analysis.score_match(
                job_id=job_id,
                resume_id=resume_id,
                threshold=threshold,
                auto_deep=auto_deep,
                run_name=payload.get("run_name"),
                legacy_run_id=legacy_run_id,
                force_rerun_pass1=force_rerun_pass1,
                force_rerun_deep=force_rerun_deep,
                max_deep_scans_per_jd=max_deep_scans_per_jd,
                deep_single_prompt=deep_single_prompt,
                ai_concurrency=ai_concurrency,
                debug_bulk_log=debug_bulk_log,
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
                debug_run_id=run_id,
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
            self._maybe_enqueue_top_deep_wave_after_standard(run_id=run_id, payload=payload)
            return {"match_id": row["id"], "score": row["match_score"], "decision": row["decision"]}

        raise ValueError(f"Unsupported job_type: {job_type}")

    def _maybe_enqueue_top_deep_wave_after_standard(self, run_id: int, payload: dict) -> None:
        try:
            if not isinstance(payload, dict):
                return
            if not bool(payload.get("deep_cap_batch_mode")):
                return
            legacy_run_id = int(payload.get("legacy_run_id") or 0)
            job_id = int(payload.get("job_id") or 0)
            threshold = int(payload.get("threshold", 50) or 50)
            deep_cap = max(0, int(payload.get("batch_deep_cap", 0) or 0))
            batch_total = max(0, int(payload.get("batch_total_for_job", 0) or 0))
            batch_key = str(payload.get("batch_group_key") or "").strip()
            if not legacy_run_id or not job_id or deep_cap <= 0 or batch_total <= 0 or not batch_key:
                return

            linked_now = self.repo.count_legacy_run_matches_for_job(run_id=legacy_run_id, job_id=job_id)
            if linked_now < batch_total:
                return

            wave_flag = f"deep-wave:{batch_key}"
            if not self.repo.try_set_group_flag(wave_flag):
                return

            rows = [
                r
                for r in self.repo.list_legacy_run_results(run_id=legacy_run_id)
                if int(r.get("job_id") or 0) == job_id
            ]
            if not rows:
                self.repo.add_run_log(run_id, "warn", "Deep-cap wave skipped: no linked matches found for JD batch.")
                return

            rows_sorted = sorted(
                rows,
                key=lambda r: (
                    -int(r.get("standard_score") if r.get("standard_score") is not None else -1),
                    -int(r.get("match_score") if r.get("match_score") is not None else -1),
                    int(r.get("resume_id") or 0),
                ),
            )
            target = rows_sorted[:deep_cap]
            target_resume_ids = [int(r.get("resume_id") or 0) for r in target if int(r.get("resume_id") or 0)]
            if not target_resume_ids:
                self.repo.add_run_log(run_id, "warn", "Deep-cap wave skipped: no eligible resume IDs.")
                return

            queued_ids = []
            for resume_id in target_resume_ids:
                run_payload = {
                    "job_id": job_id,
                    "resume_id": resume_id,
                    "threshold": threshold,
                    "auto_deep": True,
                    "run_name": payload.get("run_name"),
                    "legacy_run_id": legacy_run_id,
                    "force_rerun_pass1": False,
                    "force_rerun_deep": False,
                    "deep_single_prompt": bool(payload.get("deep_single_prompt", False)),
                    "debug_bulk_log": bool(payload.get("debug_bulk_log", False)),
                    "max_deep_scans_per_jd": 0,
                    "ai_concurrency": max(1, int(payload.get("ai_concurrency", 1) or 1)),
                    "batch_group_key": batch_key,
                    "deep_wave_from_cap": True,
                }
                queued_ids.append(int(self.repo.enqueue_run(job_type="score_match", payload=run_payload)))
            self.repo.add_run_log(
                run_id,
                "info",
                f"Deep-cap wave queued for top {len(target_resume_ids)}/{len(rows)} by Pass 1 score. Runs #{', '.join(map(str, queued_ids))}.",
            )
        except Exception as exc:
            self.repo.add_run_log(run_id, "warn", f"Failed to enqueue deep-cap wave: {exc}")

    def _checkpoint_deep_progress(self, run_id: int, payload: dict, idx: int, total: int, details: list) -> None:
        self._ensure_not_canceled(run_id)
        payload["deep_resume_from"] = int(idx)
        payload["deep_partial_details"] = list(details or [])
        pct = 10 + int((max(0, min(idx, total)) / max(1, total)) * 85)
        self.repo.update_run_payload(run_id=run_id, payload=payload)
        self.repo.update_run_result(run_id=run_id, result={"deep_partial_details": payload["deep_partial_details"]})
        self.repo.update_run_progress(run_id=run_id, progress=min(95, pct), current_step=f"deep_scan_{idx}_of_{total}")
