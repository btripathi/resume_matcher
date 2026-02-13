import json
import datetime as dt
from dataclasses import dataclass

import pandas as pd

from database import DBManager


def _parse_tags(raw_tags: str | None) -> list[str]:
    if not raw_tags:
        return []
    return [t.strip() for t in str(raw_tags).split(",") if t.strip()]


def _join_tags(tags: list[str]) -> str | None:
    cleaned = []
    seen = set()
    for tag in tags:
        value = tag.strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(value)
    return ",".join(cleaned) if cleaned else None


def _candidate_name_from_profile(profile_raw, fallback_name: str | None = None, resume_filename: str | None = None) -> str:
    parsed = {}
    if isinstance(profile_raw, dict):
        parsed = profile_raw
    elif isinstance(profile_raw, str):
        try:
            parsed = json.loads(profile_raw)
        except Exception:
            parsed = {}
    if isinstance(parsed, dict):
        name = str(parsed.get("candidate_name", "") or "").strip()
        if name:
            return name
    fallback = str(fallback_name or "").strip()
    if fallback:
        return fallback
    return str(resume_filename or "").strip()


def _as_int(value, default: int = 0, nullable: bool = False):
    if value is None:
        return None if nullable else default
    try:
        if pd.isna(value):
            return None if nullable else default
    except Exception:
        pass
    try:
        if isinstance(value, (bytes, bytearray)):
            b = bytes(value)
            # SQLite sometimes returns raw little-endian integer bytes for legacy rows.
            if len(b) in (1, 2, 4, 8):
                return int.from_bytes(b, byteorder="little", signed=False)
            txt = b.decode("utf-8", errors="ignore").strip()
            if txt:
                return int(float(txt))
            return None if nullable else default
        return int(float(value))
    except Exception:
        return None if nullable else default


@dataclass
class Repository:
    db: DBManager

    def list_jobs(self) -> list[dict]:
        df = self.db.fetch_dataframe(
            "SELECT id, filename, tags, upload_date FROM jobs ORDER BY id DESC"
        )
        return [
            {
                "id": int(row["id"]),
                "filename": row["filename"],
                "tags": _parse_tags(row.get("tags")),
                "upload_date": row.get("upload_date"),
            }
            for _, row in df.iterrows()
        ]

    def list_resumes(self) -> list[dict]:
        df = self.db.fetch_dataframe(
            "SELECT id, filename, tags, upload_date FROM resumes ORDER BY id DESC"
        )
        return [
            {
                "id": int(row["id"]),
                "filename": row["filename"],
                "tags": _parse_tags(row.get("tags")),
                "upload_date": row.get("upload_date"),
            }
            for _, row in df.iterrows()
        ]

    def get_job(self, job_id: int) -> dict | None:
        df = self.db.fetch_dataframe(
            f"SELECT id, filename, content, criteria, tags, upload_date FROM jobs WHERE id = {int(job_id)} LIMIT 1"
        )
        if df.empty:
            return None
        row = df.iloc[0]
        return {
            "id": int(row["id"]),
            "filename": row["filename"],
            "content": row["content"],
            "criteria": row["criteria"],
            "tags": _parse_tags(row.get("tags")),
            "upload_date": row.get("upload_date"),
        }

    def get_resume(self, resume_id: int) -> dict | None:
        df = self.db.fetch_dataframe(
            f"SELECT id, filename, content, profile, tags, upload_date FROM resumes WHERE id = {int(resume_id)} LIMIT 1"
        )
        if df.empty:
            return None
        row = df.iloc[0]
        return {
            "id": int(row["id"]),
            "filename": row["filename"],
            "content": row["content"],
            "profile": row["profile"],
            "tags": _parse_tags(row.get("tags")),
            "upload_date": row.get("upload_date"),
        }

    def add_job(self, filename: str, content: str, criteria: dict, tags: list[str]) -> dict:
        self.db.add_job(filename, content, criteria, tags=_join_tags(tags))
        created = self.db.get_job_by_filename(filename)
        return self.get_job(int(created["id"])) if created else {}

    def add_resume(self, filename: str, content: str, profile: dict, tags: list[str]) -> dict:
        self.db.add_resume(filename, content, profile, tags=_join_tags(tags))
        created = self.db.get_resume_by_filename(filename)
        return self.get_resume(int(created["id"])) if created else {}

    def create_run(self, run_name: str, threshold: int) -> int:
        return int(self.db.create_run(run_name, threshold=threshold))

    def link_run_match(self, run_id: int, match_id: int) -> None:
        self.db.link_run_match(run_id, match_id)

    def save_match(
        self,
        job_id: int,
        resume_id: int,
        result: dict,
        match_id: int | None = None,
        strategy: str = "Standard",
        standard_score: int | None = None,
        standard_reasoning: str | None = None,
    ) -> int:
        return int(
            self.db.save_match(
                job_id=job_id,
                resume_id=resume_id,
                data=result,
                match_id=match_id,
                strategy=strategy,
                standard_score=standard_score,
                standard_reasoning=standard_reasoning,
            )
        )

    def get_match(self, match_id: int) -> dict | None:
        df = self.db.fetch_dataframe(
            "SELECT m.id, m.job_id, m.resume_id, m.candidate_name, m.match_score, m.standard_score, "
            "m.decision, m.reasoning, m.standard_reasoning, m.missing_skills, m.match_details, m.strategy, "
            "r.profile AS resume_profile, r.filename AS resume_name "
            "FROM matches m "
            "LEFT JOIN resumes r ON r.id = m.resume_id "
            f"WHERE m.id = {int(match_id)} LIMIT 1"
        )
        if df.empty:
            return None
        row = df.iloc[0]
        return {
            "id": int(row["id"]),
            "job_id": int(row["job_id"]),
            "resume_id": int(row["resume_id"]),
            "candidate_name": _candidate_name_from_profile(
                row.get("resume_profile"),
                row.get("candidate_name"),
                row.get("resume_name"),
            ),
            "match_score": _as_int(row.get("match_score"), default=0),
            "standard_score": _as_int(row.get("standard_score"), nullable=True),
            "decision": row["decision"] or "",
            "reasoning": row["reasoning"] or "",
            "standard_reasoning": row["standard_reasoning"] or "",
            "missing_skills": json.loads(row["missing_skills"]) if row["missing_skills"] else [],
            "match_details": json.loads(row["match_details"]) if row["match_details"] else [],
            "strategy": row["strategy"] or "Standard",
        }

    def get_existing_match(self, job_id: int, resume_id: int) -> dict | None:
        return self.db.get_match_if_exists(job_id, resume_id)

    def list_tags(self) -> list[str]:
        return self.db.list_tags()

    def update_job_metadata(self, job_id: int, criteria: str | None = None, tags: list[str] | None = None) -> None:
        row = self.get_job(job_id)
        if not row:
            raise ValueError(f"Job {job_id} not found")
        if criteria is not None:
            self.db.execute_query("UPDATE jobs SET criteria = ? WHERE id = ?", (criteria, int(job_id)))
        if tags is not None:
            tags_val = _join_tags(tags)
            self.db.execute_query("UPDATE jobs SET tags = ? WHERE id = ?", (tags_val, int(job_id)))
            for t in tags or []:
                if t.strip():
                    self.db.add_tag(t.strip())

    def delete_job(self, job_id: int) -> None:
        self.db.execute_query("DELETE FROM matches WHERE job_id = ?", (int(job_id),))
        self.db.execute_query("DELETE FROM jobs WHERE id = ?", (int(job_id),))

    def update_resume_metadata(self, resume_id: int, profile: str | None = None, tags: list[str] | None = None) -> None:
        row = self.get_resume(resume_id)
        if not row:
            raise ValueError(f"Resume {resume_id} not found")
        if profile is not None:
            self.db.execute_query("UPDATE resumes SET profile = ? WHERE id = ?", (profile, int(resume_id)))
        if tags is not None:
            tags_val = _join_tags(tags)
            self.db.execute_query("UPDATE resumes SET tags = ? WHERE id = ?", (tags_val, int(resume_id)))
            for t in tags or []:
                if t.strip():
                    self.db.add_tag(t.strip())

    def delete_resume(self, resume_id: int) -> None:
        self.db.execute_query("DELETE FROM matches WHERE resume_id = ?", (int(resume_id),))
        self.db.execute_query("DELETE FROM resumes WHERE id = ?", (int(resume_id),))

    def add_tag(self, name: str) -> None:
        self.db.add_tag(name)

    def rename_tag(self, old: str, new: str) -> None:
        self.db.rename_tag(old, new)
        self.db.rename_tag_in_jobs(old, new)
        self.db.rename_tag_in_resumes(old, new)

    def delete_tag(self, name: str) -> None:
        self.db.delete_tag(name)
        self.db.delete_tag_from_jobs(name)
        self.db.delete_tag_from_resumes(name)

    def reset_all_data(self) -> None:
        self.db.execute_query("DELETE FROM matches")
        self.db.execute_query("DELETE FROM runs")
        self.db.execute_query("DELETE FROM run_matches")
        self.db.execute_query("DELETE FROM job_run_logs")
        self.db.execute_query("DELETE FROM job_runs")
        self.db.execute_query("DELETE FROM jobs")
        self.db.execute_query("DELETE FROM resumes")

    def list_matches(self, limit: int = 200) -> list[dict]:
        df = self.db.fetch_dataframe(
            "SELECT m.id, m.job_id, m.resume_id, m.candidate_name, m.match_score, m.strategy, m.decision, m.reasoning, "
            "r.profile AS resume_profile, r.filename AS resume_name "
            "FROM matches m "
            "JOIN (SELECT MAX(id) AS id FROM matches GROUP BY job_id, resume_id) latest ON latest.id = m.id "
            "LEFT JOIN resumes r ON r.id = m.resume_id "
            "ORDER BY m.id DESC LIMIT "
            f"{int(limit)}"
        )
        rows = []
        for _, row in df.iterrows():
            rows.append(
                {
                    "id": int(row["id"]),
                    "job_id": int(row["job_id"]),
                    "resume_id": int(row["resume_id"]),
                    "candidate_name": _candidate_name_from_profile(
                        row.get("resume_profile"),
                        row.get("candidate_name"),
                        row.get("resume_name"),
                    ),
                    "resume_name": row.get("resume_name") or "",
                    "match_score": _as_int(row.get("match_score"), default=0),
                    "strategy": row["strategy"] or "Standard",
                    "decision": row["decision"] or "",
                    "reasoning": row["reasoning"] or "",
                }
            )
        return rows

    def delete_legacy_run(self, run_id: int, delete_linked_matches: bool = False) -> dict:
        return self.db.delete_legacy_run(run_id=run_id, delete_linked_matches=delete_linked_matches)

    def delete_matches_by_pair(self, job_id: int, resume_id: int) -> dict:
        return self.db.delete_matches_by_pair(job_id=job_id, resume_id=resume_id)

    def get_match_summary(self, match_id: int) -> dict | None:
        df = self.db.fetch_dataframe(
            "SELECT m.id, m.job_id, m.resume_id, m.candidate_name, m.match_score, m.standard_score, m.decision, "
            "m.reasoning, m.standard_reasoning, m.strategy, m.match_details, m.missing_skills, "
            "r.profile AS resume_profile, r.filename AS resume_name "
            "FROM matches m "
            "LEFT JOIN resumes r ON r.id = m.resume_id "
            f"WHERE m.id = {int(match_id)} LIMIT 1"
        )
        if df.empty:
            return None
        row = df.iloc[0]
        return {
            "id": int(row["id"]),
            "job_id": int(row["job_id"]),
            "resume_id": int(row["resume_id"]),
            "candidate_name": _candidate_name_from_profile(
                row.get("resume_profile"),
                row.get("candidate_name"),
                row.get("resume_name"),
            ),
            "match_score": _as_int(row.get("match_score"), default=0),
            "standard_score": _as_int(row.get("standard_score"), nullable=True),
            "decision": row["decision"] or "",
            "reasoning": row["reasoning"] or "",
            "standard_reasoning": row["standard_reasoning"] or "",
            "strategy": row["strategy"] or "Standard",
            "match_details": json.loads(row["match_details"]) if row["match_details"] else [],
            "missing_skills": json.loads(row["missing_skills"]) if row["missing_skills"] else [],
        }

    def list_legacy_runs(self, limit: int = 100) -> list[dict]:
        df = self.db.fetch_dataframe(
            "SELECT id, name, threshold, created_at FROM runs ORDER BY id DESC LIMIT "
            f"{int(limit)}"
        )
        rows = []
        for _, row in df.iterrows():
            rows.append(
                {
                    "id": int(row["id"]),
                    "name": row["name"] or "",
                    "threshold": int(row["threshold"] or 50),
                    "created_at": row["created_at"] or "",
                }
            )
        return rows

    def list_legacy_run_results(self, run_id: int) -> list[dict]:
        df = self.db.fetch_dataframe(
            "SELECT m.id, m.job_id, m.resume_id, m.candidate_name, m.match_score, m.standard_score, m.decision, m.reasoning, "
            "m.strategy, j.filename AS job_name, r.filename AS resume_name, r.profile AS resume_profile "
            "FROM matches m "
            "JOIN run_matches rm ON rm.match_id = m.id "
            "JOIN jobs j ON j.id = m.job_id "
            "JOIN resumes r ON r.id = m.resume_id "
            f"WHERE rm.run_id = {int(run_id)} "
            "ORDER BY m.match_score DESC"
        )
        rows = []
        for _, row in df.iterrows():
            rows.append(
                {
                    "id": int(row["id"]),
                    "job_id": int(row["job_id"]),
                    "resume_id": int(row["resume_id"]),
                    "job_name": row["job_name"] or "",
                    "resume_name": row["resume_name"] or "",
                    "candidate_name": _candidate_name_from_profile(
                        row.get("resume_profile"),
                        row.get("candidate_name"),
                        row.get("resume_name"),
                    ),
                    "match_score": _as_int(row.get("match_score"), default=0),
                    "standard_score": _as_int(row.get("standard_score"), nullable=True),
                    "decision": row["decision"] or "",
                    "reasoning": row["reasoning"] or "",
                    "strategy": row["strategy"] or "Standard",
                }
            )
        return rows

    def enqueue_run(self, job_type: str, payload: dict) -> int:
        return int(self.db.enqueue_job_run(job_type, payload))

    def list_runs(self, limit: int = 100) -> list[dict]:
        rows = self.db.list_job_runs(limit=limit)
        now = dt.datetime.now()
        stale_after_sec = 180
        for row in rows:
            row["is_stuck"] = False
            row["stuck_seconds"] = 0
            if row.get("status") != "running":
                continue
            last_marker = row.get("last_log_at") or row.get("started_at") or row.get("created_at")
            if not last_marker:
                continue
            try:
                marker_dt = dt.datetime.fromisoformat(str(last_marker))
            except Exception:
                continue
            delta = int((now - marker_dt).total_seconds())
            row["stuck_seconds"] = max(0, delta)
            row["is_stuck"] = delta >= stale_after_sec
        return rows

    def get_run(self, run_id: int) -> dict | None:
        row = self.db.get_job_run(run_id)
        if not row:
            return None
        if row.get("status") == "running":
            now = dt.datetime.now()
            marker = row.get("last_log_at") or row.get("started_at") or row.get("created_at")
            stuck = False
            stuck_sec = 0
            if marker:
                try:
                    marker_dt = dt.datetime.fromisoformat(str(marker))
                    stuck_sec = max(0, int((now - marker_dt).total_seconds()))
                    stuck = stuck_sec >= 180
                except Exception:
                    pass
            row["is_stuck"] = stuck
            row["stuck_seconds"] = stuck_sec
        else:
            row["is_stuck"] = False
            row["stuck_seconds"] = 0
        return row

    def claim_next_run(self) -> dict | None:
        return self.db.claim_next_job_run()

    def update_run_progress(self, run_id: int, progress: int, current_step: str) -> None:
        self.db.update_job_run_progress(run_id=run_id, progress=progress, current_step=current_step)

    def update_run_payload(self, run_id: int, payload: dict) -> None:
        self.db.update_job_run_payload(run_id=run_id, payload=payload)

    def update_run_result(self, run_id: int, result: dict) -> None:
        self.db.update_job_run_result(run_id=run_id, result=result)

    def complete_run(self, run_id: int, result: dict) -> None:
        self.db.complete_job_run(run_id=run_id, result=result)

    def fail_run(self, run_id: int, error: str) -> None:
        self.db.fail_job_run(run_id=run_id, error_message=error)

    def requeue_run(self, run_id: int, payload: dict | None = None, current_step: str = "requeued") -> bool:
        return bool(self.db.requeue_job_run(run_id=run_id, payload=payload, current_step=current_step))

    def add_run_log(self, run_id: int, level: str, message: str) -> int:
        return self.db.append_job_run_log(run_id=run_id, level=level, message=message)

    def list_run_logs(self, run_id: int, limit: int = 500) -> list[dict]:
        # Return ascending timeline for UI readability.
        return list(reversed(self.db.list_job_run_logs(run_id=run_id, limit=limit)))

    def dashboard_snapshot(self) -> dict:
        jobs = self.list_jobs()
        resumes = self.list_resumes()
        matches = self.list_matches(limit=200)
        runs = self.list_runs(limit=200)
        running = sum(1 for r in runs if r.get("status") == "running")
        queued = sum(1 for r in runs if r.get("status") == "queued")
        failed = sum(1 for r in runs if r.get("status") == "failed")

        jobs_total = int(self.db.fetch_dataframe("SELECT COUNT(*) AS c FROM jobs").iloc[0]["c"])
        resumes_total = int(self.db.fetch_dataframe("SELECT COUNT(*) AS c FROM resumes").iloc[0]["c"])
        matches_total = int(self.db.fetch_dataframe("SELECT COUNT(*) AS c FROM matches").iloc[0]["c"])
        bg_runs_total = int(self.db.fetch_dataframe("SELECT COUNT(*) AS c FROM job_runs").iloc[0]["c"])
        legacy_runs_total = int(self.db.fetch_dataframe("SELECT COUNT(*) AS c FROM runs").iloc[0]["c"])

        return {
            "counts": {
                "jobs": jobs_total,
                "resumes": resumes_total,
                "matches": matches_total,
                "runs": bg_runs_total,
                "legacy_runs": legacy_runs_total,
                "running_runs": running,
                "queued_runs": queued,
                "failed_runs": failed,
            },
            "recent": {
                "jobs": jobs[:25],
                "resumes": resumes[:25],
                "matches": matches[:25],
                "runs": runs[:25],
            },
        }
