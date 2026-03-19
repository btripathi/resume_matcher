"""Tests for database.py — DBManager."""

import json
import sqlite3


def test_tables_created(db):
    """All expected tables exist after init."""
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    names = {row[0] for row in c.fetchall()}
    conn.close()
    for expected in ("jobs", "resumes", "matches", "job_runs", "tags", "runs", "run_matches", "job_run_logs"):
        assert expected in names, f"Table {expected} missing"


def test_wal_mode(db):
    """WAL journal mode is enabled."""
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("PRAGMA journal_mode")
    mode = c.fetchone()[0]
    conn.close()
    assert mode.lower() == "wal"


def test_add_and_get_job(db):
    db.add_job("jd1.pdf", "Some JD content", {"must_have_skills": ["Python"]}, tags="eng")
    row = db.get_job_by_filename("jd1.pdf")
    assert row is not None
    assert row["id"] >= 1


def test_add_and_get_resume(db):
    db.add_resume("cv.pdf", "Resume text", {"candidate_name": "Alice"}, tags="dev")
    row = db.get_resume_by_filename("cv.pdf")
    assert row is not None
    assert row["id"] >= 1


def test_save_and_get_match(db):
    db.add_job("jd.pdf", "JD text", {})
    db.add_resume("cv.pdf", "Resume text", {})
    job = db.get_job_by_filename("jd.pdf")
    resume = db.get_resume_by_filename("cv.pdf")
    data = {
        "candidate_name": "Bob",
        "match_score": 75,
        "decision": "Review",
        "reasoning": "Decent match.",
        "missing_skills": [],
        "match_details": [],
    }
    match_id = db.save_match(job["id"], resume["id"], data)
    assert match_id >= 1
    row = db.get_match_if_exists(job["id"], resume["id"])
    assert row is not None
    assert row["match_score"] == 75


def test_tag_add_list_delete(db):
    db.add_tag("backend")
    db.add_tag("frontend")
    tags = db.list_tags()
    assert "backend" in tags
    assert "frontend" in tags
    db.delete_tag("frontend")
    tags = db.list_tags()
    assert "frontend" not in tags
    assert "backend" in tags


def test_tag_rename(db):
    db.add_tag("old_tag")
    db.rename_tag("old_tag", "new_tag")
    tags = db.list_tags()
    assert "new_tag" in tags
    assert "old_tag" not in tags


def test_tag_add_empty_ignored(db):
    db.add_tag("")
    db.add_tag("   ")
    assert db.list_tags() == []


def test_checkpoint_job_run(db):
    run_id = db.enqueue_job_run("score_match", {"job_id": 1})
    db.checkpoint_job_run(
        run_id,
        payload={"job_id": 1, "deep_resume_from": 3},
        result={"partial": True},
        progress=42,
        current_step="deep_scan_3_of_10",
    )
    row = db.get_job_run(run_id)
    assert row["progress"] == 42
    assert row["current_step"] == "deep_scan_3_of_10"
    assert row["payload"]["deep_resume_from"] == 3
    assert row["result"]["partial"] is True


def test_enqueue_claim_complete(db):
    run_id = db.enqueue_job_run("ingest_job", {"filename": "x.pdf"})
    assert run_id >= 1
    row = db.get_job_run(run_id)
    assert row["status"] == "queued"

    claimed = db.claim_next_job_run()
    assert claimed is not None
    assert claimed["id"] == run_id
    assert claimed["status"] == "running"

    ok = db.complete_job_run(run_id, result={"done": True})
    assert ok is True
    row = db.get_job_run(run_id)
    assert row["status"] == "completed"
    assert row["progress"] == 100


def test_save_match_update(db):
    """save_match with match_id updates instead of inserting."""
    db.add_job("jd.pdf", "content", {})
    db.add_resume("cv.pdf", "content", {})
    job = db.get_job_by_filename("jd.pdf")
    resume = db.get_resume_by_filename("cv.pdf")
    data = {
        "candidate_name": "Carol",
        "match_score": 60,
        "decision": "Review",
        "reasoning": "First pass",
        "missing_skills": [],
        "match_details": [],
    }
    mid = db.save_match(job["id"], resume["id"], data)
    data["match_score"] = 90
    data["decision"] = "Move Forward"
    mid2 = db.save_match(job["id"], resume["id"], data, match_id=mid)
    assert mid2 == mid
    row = db.get_match_if_exists(job["id"], resume["id"])
    assert row["match_score"] == 90
