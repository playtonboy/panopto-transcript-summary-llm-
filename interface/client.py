"""How the Streamlit interface talks to the orchestrator (Task 6, SCRUM-52).

The interface only sends jobs and reads their status. It never calls LM Studio or summarize() itself.
"""

import time
from collections.abc import Callable

import requests

import config
from summarizer.summarize import Summary  # only the data class, to hold the result
from summarizer.transcript import Transcript

POLL_S = 0.5  # how often the progress bar is updated (seconds)


class JobFailed(RuntimeError):
    """The summary could not be made. The message is shown to the student."""


def is_running() -> bool:
    try:
        return requests.get(f"{config.ORCHESTRATOR_URL}/health", timeout=3).ok
    except requests.RequestException:
        return False


def submit(transcript: Transcript, detail_level: str, language: str) -> str:
    """Put a new job in the queue and return its id."""
    response = requests.post(
        f"{config.ORCHESTRATOR_URL}/jobs",
        json={
            "text": transcript.text,
            "title": transcript.title,
            "speakers": transcript.speakers,
            "detail_level": detail_level,
            "language": language,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["id"]


def wait_for_summary(job_id: str, on_progress: Callable[[str, float], None]) -> Summary:
    """Ask the orchestrator how the job is doing until it is done, and show the progress meanwhile."""
    while True:
        response = requests.get(f"{config.ORCHESTRATOR_URL}/jobs/{job_id}", timeout=10)
        response.raise_for_status()
        job = response.json()
        if job["status"] == "done":
            return Summary(title=job["title"], body=job["body"])
        if job["status"] == "failed":
            raise JobFailed(job["error"])
        on_progress(job["message"], job["progress"])
        time.sleep(POLL_S)