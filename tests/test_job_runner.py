"""Tests for the JobRunner service."""

import time

from backend.services.job_runner import JobRunner


def test_recompute_paused_no_runs(repo, mock_llm):
    from backend.services.analysis import AnalysisService
    analysis = AnalysisService(repo=repo, llm=mock_llm)
    runner = JobRunner(repo=repo, analysis=analysis)
    assert runner.recompute_paused() is False


def test_recompute_paused_with_paused_run(repo, mock_llm):
    from backend.services.analysis import AnalysisService
    analysis = AnalysisService(repo=repo, llm=mock_llm)
    runner = JobRunner(repo=repo, analysis=analysis)

    run_id = repo.enqueue_run(job_type="ingest_job", payload={"filename": "x.pdf"})
    # Transition: queued -> paused
    repo.pause_run(run_id=run_id, reason="test pause")
    assert runner.recompute_paused() is True


def test_runner_start_stop(repo, mock_llm):
    from backend.services.analysis import AnalysisService
    analysis = AnalysisService(repo=repo, llm=mock_llm)
    runner = JobRunner(repo=repo, analysis=analysis, poll_seconds=0.1, worker_pool_size=1)
    runner.start()
    assert any(t.is_alive() for t in runner._threads)
    runner.stop()
    # After stop, threads should no longer be alive.
    assert all(not t.is_alive() for t in runner._threads)


def test_claim_next_run(repo):
    run_id = repo.enqueue_run(job_type="ingest_resume", payload={"filename": "cv.pdf"})
    claimed = repo.claim_next_run()
    assert claimed is not None
    assert claimed["id"] == run_id
    assert claimed["status"] == "running"

    # Second claim should return None (no more queued runs).
    second = repo.claim_next_run()
    assert second is None


def test_runner_processes_ingest_job(repo, mock_llm):
    """Runner picks up and completes an ingest_job run end-to-end."""
    from backend.services.analysis import AnalysisService
    analysis = AnalysisService(repo=repo, llm=mock_llm)
    runner = JobRunner(repo=repo, analysis=analysis, poll_seconds=0.1, worker_pool_size=1)

    run_id = repo.enqueue_run(
        job_type="ingest_job",
        payload={"filename": "runner_jd.pdf", "content": "Engineer\nmust have: Go", "tags": []},
    )
    runner.start()
    # Wait for runner to pick up and complete the run.
    deadline = time.time() + 5
    while time.time() < deadline:
        row = repo.get_run(run_id)
        if row and row["status"] in ("completed", "failed"):
            break
        time.sleep(0.1)
    runner.stop()

    row = repo.get_run(run_id)
    assert row is not None
    assert row["status"] == "completed"
