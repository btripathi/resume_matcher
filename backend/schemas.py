from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class JobIn(BaseModel):
    filename: str
    content: str
    tags: list[str] = Field(default_factory=list)


class ResumeIn(BaseModel):
    filename: str
    content: str
    tags: list[str] = Field(default_factory=list)


class JobOut(BaseModel):
    id: int
    filename: str
    tags: list[str] = Field(default_factory=list)
    upload_date: str | None = None


class ResumeOut(BaseModel):
    id: int
    filename: str
    tags: list[str] = Field(default_factory=list)
    upload_date: str | None = None


class ScoreMatchRequest(BaseModel):
    job_id: int
    resume_id: int
    run_name: str | None = None
    legacy_run_id: int | None = None
    threshold: int = 50
    auto_deep: bool = False
    force_rerun_pass1: bool = False
    force_rerun_deep: bool = False


class MatchOut(BaseModel):
    id: int
    job_id: int
    resume_id: int
    candidate_name: str
    match_score: int
    decision: str
    strategy: str
    reasoning: str | None = None
    missing_skills: list[str] = Field(default_factory=list)
    standard_score: int | None = None
    standard_reasoning: str | None = None
    match_details: list[dict[str, Any]] = Field(default_factory=list)


class RunRequest(BaseModel):
    job_type: str = Field(description="ingest_job | ingest_resume | score_match")
    payload: dict[str, Any] = Field(default_factory=dict)


class RunOut(BaseModel):
    id: int
    job_type: str
    status: str
    progress: int = 0
    current_step: str | None = None
    error: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    last_log_at: str | None = None
    is_stuck: bool = False
    stuck_seconds: int = 0


class RunLogOut(BaseModel):
    id: int
    run_id: int
    level: str
    message: str
    created_at: str
