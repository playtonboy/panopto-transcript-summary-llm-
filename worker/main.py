import socket
import argparse
import time
from typing import List, Optional

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


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Read the worker's name and settings from the command line (SCRUM-56)."""
    parser = argparse.ArgumentParser(description="AI worker: summarizes jobs from the orchestrator with LM Studio.")
    parser.add_argument("name", nargs="?", default=f"{socket.gethostname()}-{time.time_ns() % 10000}")
    parser.add_argument("--model", default=config.MODEL_NAME, help="LM Studio API id of the model to use")
    parser.add_argument("--lmstudio-url", default=config.LMSTUDIO_BASE_URL, help="LM Studio server address")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    config.MODEL_NAME, config.LMSTUDIO_BASE_URL = args.model, args.lmstudio_url
    print(f"Worker {args.name} uses model '{config.MODEL_NAME}' at {config.LMSTUDIO_BASE_URL}")
    warning = llm_client.model_warning()
    if warning:
        print("Warning: " + warning)
    print(f"Waiting for jobs from {config.ORCHESTRATOR_URL} (stop with Ctrl+C)")
    while True:
        try:
            if not run_one_job(args.name):
                time.sleep(config.WORKER_POLL_S)
        except requests.RequestException:
            print("Cannot reach the orchestrator, trying again in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    main()