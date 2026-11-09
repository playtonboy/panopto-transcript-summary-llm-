
import time

from fastapi.testclient import TestClient

import config
from orchestrator import main as orchestrator


def test_worker_crash_retries_once(monkeypatch):
    client = TestClient(orchestrator.app)

    # Create a new summarization job.
    response = client.post("/jobs", json={"text": "Test lecture transcript"})
    job_id = response.json()["id"]

    # A worker picks up the job for the first time.
    response = client.post("/jobs/next?worker=test-worker")
    assert response.status_code == 200
    assert response.json()["id"] == job_id

    # Simulate the worker stopping long enough ago.
    with orchestrator.lock:
        orchestrator.db.execute(
            "UPDATE jobs SET updated = ? WHERE id = ?",
            (time.time() - config.JOB_STALE_S - 10, job_id),
        )

    # Checking the job should put it back in the queue.
    response = client.get(f"/jobs/{job_id}")
    assert response.json()["status"] == "queued"

    # Another worker picks up the retried job.
    response = client.post("/jobs/next?worker=second-worker")
    assert response.status_code == 200
    assert response.json()["id"] == job_id

    # Simulate the second worker stopping too.
    with orchestrator.lock:
        orchestrator.db.execute(
            "UPDATE jobs SET updated = ? WHERE id = ?",
            (time.time() - config.JOB_STALE_S - 10, job_id),
        )

    # After two attempts, the job must fail.
    response = client.get(f"/jobs/{job_id}")
    assert response.json()["status"] == "failed"


def test_orchestrator_down(monkeypatch):
    import requests
    from interface import client

    def connection_error(*args, **kwargs):
        raise requests.ConnectionError("Connection refused")

    monkeypatch.setattr(client.requests, "get", connection_error)

    assert client.health() is None


def test_interface_timeout(monkeypatch):
    from interface import client

    monkeypatch.setattr(config, "INTERFACE_TIMEOUT_S", 0)

    def on_progress(message, fraction):
        pass

    try:
        client.wait_for_summary("test-job", on_progress)
        assert False, "Expected JobFailed"
    except client.JobFailed as error:
        assert "too long" in str(error).lower()


def test_health_counts_active_workers(monkeypatch):
    client = TestClient(orchestrator.app)

    with orchestrator.lock:
        orchestrator.workers_seen.clear()

    # No workers have contacted the orchestrator.
    assert client.get("/health").json()["workers"] == 0

    # Simulate a worker requesting a job.
    client.post("/jobs/next?worker=health-test-worker")
    assert client.get("/health").json()["workers"] == 1

    # Simulate the worker becoming inactive.
    with orchestrator.lock:
        orchestrator.workers_seen["health-test-worker"] = (
            time.time() - config.WORKER_SEEN_S - 10
        )

    assert client.get("/health").json()["workers"] == 0
