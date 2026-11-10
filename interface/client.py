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

NOT_RUNNING = "The summarizer service is not running. Please try again later."
NO_WORKER = "Waiting for an AI worker to become available..."


class JobFailed(RuntimeError):
    """The summary could not be made. The message is shown to the student."""


def is_running() -> bool:
    try:
        return requests.get(f"{config.ORCHESTRATOR_URL}/health", timeout=3).ok
    except requests.RequestException:
        return False

def health():
    """Get the orchestrator status and number of active workers."""
    try:
        response = requests.get(
            f"{config.ORCHESTRATOR_URL}/health",
            timeout=3,
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return None



def submit(transcript: Transcript, detail_level: str, language: str) -> str:
    """Put a new job in the queue and return its id."""
    try:
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
    except (requests.RequestException, ValueError, KeyError) as exc:
        raise JobFailed(NOT_RUNNING) from exc




def wait_for_summary(job_id: str, on_progress: Callable[[str, float], None]) -> Summary:
    """Wait for a summary, handling connection failures and timeouts."""
    deadline = time.monotonic() + config.INTERFACE_TIMEOUT_S

    while time.monotonic() < deadline:
        try:
            response = requests.get(
                f"{config.ORCHESTRATOR_URL}/jobs/{job_id}",
                timeout=10,
            )
            response.raise_for_status()
            job = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise JobFailed(NOT_RUNNING) from exc

        if job["status"] == "done":
            return Summary(title=job["title"], body=job["body"])

        if job["status"] == "failed":
            raise JobFailed(job.get("error") or "The summary could not be completed.")

        if job["status"] == "queued":
            status = health()
            if status is None:
                raise JobFailed(NOT_RUNNING)
            if status.get("workers", 0) == 0:
                on_progress(NO_WORKER, job["progress"])
            else:
                on_progress(job["message"], job["progress"])
        else:
            on_progress(job["message"], job["progress"])

        time.sleep(min(POLL_S, max(0, deadline - time.monotonic())))

    raise JobFailed("The summary took too long. Please try again later.")
