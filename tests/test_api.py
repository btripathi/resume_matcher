"""Tests for the FastAPI app endpoints."""

import pytest


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_job(client):
    resp = client.post("/v1/jobs", json={
        "filename": "jd_test.pdf",
        "content": "Software Engineer\nmust have: Python, FastAPI",
        "tags": ["eng"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "jd_test.pdf"
    assert data["id"] >= 1


def test_list_jobs(client):
    client.post("/v1/jobs", json={"filename": "a.pdf", "content": "JD content"})
    resp = client.get("/v1/jobs")
    assert resp.status_code == 200
    jobs = resp.json()
    assert isinstance(jobs, list)
    assert len(jobs) >= 1


def test_create_resume(client):
    resp = client.post("/v1/resumes", json={
        "filename": "cv_test.pdf",
        "content": "Alice\nalice@test.com\nSkills: Python, SQL",
        "tags": [],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "cv_test.pdf"
    assert data["id"] >= 1


def test_list_resumes(client):
    client.post("/v1/resumes", json={"filename": "r.pdf", "content": "Resume text"})
    resp = client.get("/v1/resumes")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_score_match(client):
    # Create a job and resume first.
    job_resp = client.post("/v1/jobs", json={
        "filename": "jd_score.pdf",
        "content": "Engineer\nmust have: Python",
    })
    resume_resp = client.post("/v1/resumes", json={
        "filename": "cv_score.pdf",
        "content": "Bob\nSkills: Python, Java",
    })
    job_id = job_resp.json()["id"]
    resume_id = resume_resp.json()["id"]
    resp = client.post("/v1/matches/score", json={
        "job_id": job_id,
        "resume_id": resume_id,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "match_score" in data
    assert "decision" in data
    assert data["job_id"] == job_id
    assert data["resume_id"] == resume_id


def test_settings_state(client):
    resp = client.get("/v1/settings/state")
    assert resp.status_code == 200
    data = resp.json()
    expected_keys = ["lm_base_url", "lm_api_key", "ocr_enabled", "write_mode", "run_queue_paused"]
    for key in expected_keys:
        assert key in data, f"Missing key: {key}"


def test_create_run(client):
    # Must have a job+resume to create a valid score_match run.
    job_resp = client.post("/v1/jobs", json={"filename": "j.pdf", "content": "JD text"})
    resume_resp = client.post("/v1/resumes", json={"filename": "r.pdf", "content": "Resume text"})
    resp = client.post("/v1/runs", json={
        "job_type": "score_match",
        "payload": {
            "job_id": job_resp.json()["id"],
            "resume_id": resume_resp.json()["id"],
        },
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_type"] == "score_match"
    assert data["status"] == "queued"


def test_list_runs(client):
    resp = client.get("/v1/runs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_run_invalid_type(client):
    resp = client.post("/v1/runs", json={
        "job_type": "invalid_type",
        "payload": {},
    })
    assert resp.status_code == 400
