
"""Integration tests across the three services (Task 6, SCRUM-54).

These tests use a real orchestrator, background AI workers,
and a fake LM Studio to test the complete summarization process.
"""

import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn

import config
import worker.main
from fake_lmstudio import start_fake_server
from interface import client
from orchestrator.main import app, db
from summarizer.transcript import parse

SAMPLE = parse(
    (Path(__file__).parent / "data" / "sample_transcript.txt").read_text(
        encoding="utf-8"
    )
)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def orchestrator(monkeypatch):
    """Start a real orchestrator in the background for one test."""
    db.execute("DELETE FROM jobs")
    port = free_port()

    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    )

    threading.Thread(target=server.run, daemon=True).start()

    while not server.started:
        time.sleep(0.01)

    monkeypatch.setattr(
        config, "ORCHESTRATOR_URL", f"http://127.0.0.1:{port}"
    )

    yield

    server.should_exit = True


@pytest.fixture
def lm_studio(monkeypatch):
    """Start a fake LM Studio server for testing."""
    servers = []

    def start(**options):
        server, url = start_fake_server(**options)
        servers.append(server)

        monkeypatch.setattr(config, "LMSTUDIO_BASE_URL", url)

    yield start

    for server in servers:
        server.shutdown()


@pytest.fixture
def workers():
    """Start background AI workers for testing."""
    stop = threading.Event()
    threads = []

    def start(*names):
        for name in names:
            def loop(name=name):
                while not stop.is_set():
                    if not worker.main.run_one_job(name):
                        time.sleep(0.05)

            thread = threading.Thread(target=loop, daemon=True)
            thread.start()
            threads.append(thread)

        return threads

    yield start

    stop.set()
    for thread in threads:
        thread.join(timeout=2)


def summarize_through_the_services(detail_level="Short"):
    job_id = client.submit(
        SAMPLE,
        detail_level=detail_level,
        language="English"
    )

    return client.wait_for_summary(
        job_id,
        on_progress=lambda message, fraction: None
    )


def test_a_job_goes_from_the_interface_through_a_worker_and_back(
    orchestrator, lm_studio, workers
):
    lm_studio()
    workers("a")

    summary = summarize_through_the_services()

    assert "## Main topics" in summary.body
    assert "- Software testing" in summary.body
    assert summary.title == SAMPLE.title


def test_two_workers_share_the_jobs(orchestrator, lm_studio, workers):
    lm_studio(delay_s=0.1)
    workers("a", "b")

    job_ids = [
        client.submit(SAMPLE, detail_level="Short", language="English")
        for _ in range(4)
    ]

    for job_id in job_ids:
        client.wait_for_summary(
            job_id,
            on_progress=lambda message, fraction: None
        )

    used = {row["worker"] for row in db.execute("SELECT worker FROM jobs")}

    assert used == {"a", "b"}


def test_lm_studio_problems_reach_the_student_as_a_message(
    orchestrator, lm_studio, workers
):
    lm_studio(status=500)
    workers("a")

    with pytest.raises(client.JobFailed, match="returned 500"):
        summarize_through_the_services()


def test_one_broken_job_does_not_stop_the_worker(
    orchestrator, lm_studio, workers, monkeypatch
):
    lm_studio()
    calls = []

    def broken_once(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("something unexpected")
        return real_summarize(*args, **kwargs)

    real_summarize = worker.main.summarize
    monkeypatch.setattr(worker.main, "summarize", broken_once)

    (thread,) = workers("a")

    with pytest.raises(client.JobFailed, match="unexpected error"):
        summarize_through_the_services()

    assert thread.is_alive()

    assert "- Software testing" in summarize_through_the_services().body
