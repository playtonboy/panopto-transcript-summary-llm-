"""AI worker (Task 6, SCRUM-51): takes jobs from the orchestrator and summarizes them with LM Studio.

Run with:  python -m worker.main
Start it in a second terminal to get a second worker: two lectures are then summarized at the same time.
"""

import socket
import sys
import time

import requests

import config
from summarizer import llm_client
from summarizer.summarize import summarize
from summarizer.transcript import Transcript


def run_one_job(name: str) -> bool:
    """Ask for one job and do it. Returns False when there was nothing to do."""
    response = requests.post(f"{config.ORCHESTRATOR_URL}/jobs/next", params={"worker": name}, timeout=10)
    if response.status_code == 204:
        return False
    response.raise_for_status()
    job = response.json()
    url = f"{config.ORCHESTRATOR_URL}/jobs/{job['id']}"

    def report_progress(message: str, fraction: float) -> None:
        requests.post(f"{url}/progress", json={"fraction": fraction, "message": message}, timeout=10)

    transcript = Transcript(text=job["text"], title=job["title"], speakers=job["speakers"])
    try:
        summary = summarize(
            transcript,
            detail_level=job["detail_level"],
            language=job["language"],
            on_progress=report_progress,
        )
    except llm_client.LLMError as error:  # LM Studio down, too slow, ... : the message is meant for the student
        requests.post(f"{url}/error", json={"message": str(error)}, timeout=10)
    except Exception:
        requests.post(
            f"{url}/error",
            json={"message": "An unexpected error occurred while generating the summary."},
            timeout=10,
        )
    else:
        requests.post(f"{url}/result", json={"title": summary.title, "body": summary.body}, timeout=10)
    return True


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else f"{socket.gethostname()}-{time.time_ns() % 10000}"
    print(f"Worker {name} is waiting for jobs from {config.ORCHESTRATOR_URL} (stop with Ctrl+C)")
    while True:
        try:
            if not run_one_job(name):
                time.sleep(config.WORKER_POLL_S)
        except requests.RequestException:
            print("Cannot reach the orchestrator. Retrying in 5 seconds...")
            time.sleep(5)


if __name__ == "__main__":
    main()