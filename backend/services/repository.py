import json
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
            "SELECT id, job_id, resume_id, candidate_name, match_score, standard_score, "
            "decision, reasoning, standard_reasoning, missing_skills, match_details, strategy "
            f"FROM matches WHERE id = {int(match_id)} LIMIT 1"
        )
        if df.empty:
            return None
        row = df.iloc[0]
        return {
            "id": int(row["id"]),
            "job_id": int(row["job_id"]),
            "resume_id": int(row["resume_id"]),
            "candidate_name": row["candidate_name"],
            "match_score": int(row["match_score"] or 0),
            "standard_score": int(row["standard_score"]) if pd.notna(row["standard_score"]) else None,
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
            "SELECT id, job_id, resume_id, candidate_name, match_score, strategy, decision, reasoning "
            "FROM matches ORDER BY id DESC LIMIT "
            f"{int(limit)}"
        )
        rows = []
        for _, row in df.iterrows():
            rows.append(
                {
                    "id": int(row["id"]),
                    "job_id": int(row["job_id"]),
                    "resume_id": int(row["resume_id"]),
                    "candidate_name": row["candidate_name"] or "",
                    "match_score": int(row["match_score"] or 0),
                    "strategy": row["strategy"] or "Standard",
                    "decision": row["decision"] or "",
                    "reasoning": row["reasoning"] or "",
                }
            )
        return rows

    def get_match_summary(self, match_id: int) -> dict | None:
        df = self.db.fetch_dataframe(
            "SELECT id, job_id, resume_id, candidate_name, match_score, standard_score, decision, "
            "reasoning, standard_reasoning, strategy, match_details, missing_skills "
            f"FROM matches WHERE id = {int(match_id)} LIMIT 1"
        )
        if df.empty:
            return None
        row = df.iloc[0]
        return {
            "id": int(row["id"]),
            "job_id": int(row["job_id"]),
            "resume_id": int(row["resume_id"]),
            "candidate_name": row["candidate_name"] or "",
            "match_score": int(row["match_score"] or 0),
            "standard_score": int(row["standard_score"]) if pd.notna(row["standard_score"]) else None,
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
            "m.strategy, j.filename AS job_name, r.filename AS resume_name "
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
                    "candidate_name": row["candidate_name"] or "",
                    "match_score": int(row["match_score"] or 0),
                    "standard_score": int(row["standard_score"]) if pd.notna(row["standard_score"]) else None,
                    "decision": row["decision"] or "",
                    "reasoning": row["reasoning"] or "",
                    "strategy": row["strategy"] or "Standard",
                }
            )
        return rows

    def enqueue_run(self, job_type: str, payload: dict) -> int:
        return int(self.db.enqueue_job_run(job_type, payload))

    def list_runs(self, limit: int = 100) -> list[dict]:
        return self.db.list_job_runs(limit=limit)

    def get_run(self, run_id: int) -> dict | None:
        return self.db.get_job_run(run_id)

    def claim_next_run(self) -> dict | None:
        return self.db.claim_next_job_run()

    def update_run_progress(self, run_id: int, progress: int, current_step: str) -> None:
        self.db.update_job_run_progress(run_id=run_id, progress=progress, current_step=current_step)

    def complete_run(self, run_id: int, result: dict) -> None:
        self.db.complete_job_run(run_id=run_id, result=result)

    def fail_run(self, run_id: int, error: str) -> None:
        self.db.fail_job_run(run_id=run_id, error_message=error)

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
