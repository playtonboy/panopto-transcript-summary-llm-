import pytest
from fastapi.testclient import TestClient

from orchestrator.main import app, db, workers_seen

client = TestClient(app)


@pytest.fixture(autouse=True)
def empty_queue():
    db.execute("DELETE FROM jobs")  # every test starts with an empty queue
    workers_seen.clear()


def new_job(text="Good morning everyone, today we talk about testing."):
    response = client.post("/jobs", json={"text": text, "title": "Lecture 3", "detail_level": "Short"})
    assert response.status_code == 201
    return response.json()["id"]


def test_a_new_job_is_queued():
    job = client.get(f"/jobs/{new_job()}").json()
    assert job["status"] == "queued"
    assert job["progress"] == 0


def test_unknown_job_gives_404():
    assert client.get("/jobs/does-not-exist").status_code == 404


def test_health_counts_the_workers_that_asked_for_work():
    assert client.get("/health").json() == {"status": "ok", "workers": 0}
    client.post("/jobs/next?worker=a")
    client.post("/jobs/next?worker=b")
    assert client.get("/health").json()["workers"] == 2


def test_worker_gets_nothing_when_the_queue_is_empty():
    assert client.post("/jobs/next").status_code == 204


def test_jobs_are_handed_out_oldest_first_and_only_once():
    first, second = new_job("first job"), new_job("second job")
    assert client.post("/jobs/next?worker=a").json()["id"] == first
    assert client.post("/jobs/next?worker=b").json()["id"] == second
    assert client.post("/jobs/next?worker=c").status_code == 204
    assert client.get(f"/jobs/{first}").json()["status"] == "running"


def test_progress_and_result_reach_the_interface():
    job_id = new_job()
    work = client.post("/jobs/next").json()
    assert work["title"] == "Lecture 3" and work["detail_level"] == "Short"

    client.post(f"/jobs/{job_id}/progress", json={"fraction": 0.5, "message": "Writing the summary..."})
    assert client.get(f"/jobs/{job_id}").json()["message"] == "Writing the summary..."

    client.post(f"/jobs/{job_id}/result", json={"title": "Lecture 3", "body": "## Summary\n- point"})
    job = client.get(f"/jobs/{job_id}").json()
    assert job["status"] == "done"
    assert job["body"] == "## Summary\n- point"


def test_transcript_is_deleted_once_the_job_is_finished():
    job_id = new_job()
    client.post("/jobs/next")
    client.post(f"/jobs/{job_id}/error", json={"message": "LM Studio is not running."})
    assert client.get(f"/jobs/{job_id}").json()["error"] == "LM Studio is not running."
    assert db.execute("SELECT text FROM jobs WHERE id = ?", (job_id,)).fetchone()["text"] is None