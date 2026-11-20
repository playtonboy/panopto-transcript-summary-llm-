"""Orchestrator: keeps the job queue in memory and gives each job to one worker."""

import json
import sqlite3
import threading
import time
import uuid
from typing import List

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

import config

app = FastAPI(title="Lecture summarizer orchestrator")

# The queue lives in memory only, so transcripts are never written to disk.
db = sqlite3.connect(":memory:", check_same_thread=False)
db.row_factory = sqlite3.Row
lock = threading.Lock()  # one request at a time touches the table
workers_seen = {}  # worker name -> last time it asked for work
db.execute(
    """CREATE TABLE jobs (
        id TEXT PRIMARY KEY,
        status TEXT NOT NULL,              -- queued, running, done or failed
        text TEXT, title TEXT, speakers TEXT, detail_level TEXT, language TEXT,
        progress REAL NOT NULL DEFAULT 0,
        message TEXT NOT NULL DEFAULT 'Waiting for a worker...',
        result_title TEXT, result_body TEXT, error TEXT,
        worker TEXT,
        attempts INTEGER NOT NULL DEFAULT 0,
        created REAL NOT NULL, updated REAL NOT NULL
    )"""
)


class JobRequest(BaseModel):
    """A summary request from the interface."""
    text: str
    title: str = ""
    speakers: List[str] = []
    detail_level: str = config.DEFAULT_DETAIL_LEVEL
    language: str = config.DEFAULT_OUTPUT_LANGUAGE


class Progress(BaseModel):
    """A progress update from a worker."""
    fraction: float
    message: str


class Result(BaseModel):
    """A finished summary from a worker."""
    title: str
    body: str


class Failure(BaseModel):
    """An error message from a worker."""
    message: str


def _requeue_stale_jobs():
    """Retry jobs whose worker stopped responding, up to one retry, and forget old finished jobs."""
    now = time.time()
    db.execute(
        "DELETE FROM jobs WHERE status IN ('done', 'failed') AND updated < ?",
        (now - config.JOB_KEEP_S,),
    )
    cutoff = now - config.JOB_STALE_S

    stale_jobs = db.execute(
        "SELECT id, attempts FROM jobs WHERE status = 'running' AND updated < ?",
        (cutoff,),
    ).fetchall()

    for job in stale_jobs:
        if job["attempts"] < config.JOB_MAX_ATTEMPTS:
            db.execute(
                "UPDATE jobs SET status = 'queued', worker = NULL, progress = 0, "
                "message = 'The worker stopped. Trying again...', updated = ? WHERE id = ?",
                (time.time(), job["id"]),
            )
        else:
            db.execute(
                "UPDATE jobs SET status = 'failed', message = 'Failed', "
                "error = 'The worker stopped responding after two attempts.', "
                "text = NULL, updated = ? WHERE id = ?",
                (time.time(), job["id"]),
            )


def _get(job_id: str) -> sqlite3.Row:
    row = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Unknown job")
    return row


def _is_current_worker(row: sqlite3.Row, worker: str) -> bool:
    # a worker whose job was handed to another worker must not change it any more
    return not worker or row["worker"] == worker


@app.get("/health")
def health():
    """How many workers asked for work in the last WORKER_SEEN_S seconds."""
    recent = time.time() - config.WORKER_SEEN_S
    return {"status": "ok", "workers": sum(seen > recent for seen in workers_seen.values())}


@app.post("/jobs", status_code=201)
def create_job(job: JobRequest):
    """Queue a new job and return its id."""
    job_id = uuid.uuid4().hex
    now = time.time()
    with lock:
        db.execute(
            "INSERT INTO jobs (id, status, text, title, speakers, detail_level, language, created, updated) "
            "VALUES (?, 'queued', ?, ?, ?, ?, ?, ?, ?)",
            (job_id, job.text, job.title, json.dumps(job.speakers), job.detail_level, job.language, now, now),
        )
    return {"id": job_id}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    """Status, progress and result of one job."""
    with lock:
        _requeue_stale_jobs()
        row = _get(job_id)
    return {
        "id": row["id"],
        "status": row["status"],
        "progress": row["progress"],
        "message": row["message"],
        "title": row["result_title"],
        "body": row["result_body"],
        "error": row["error"],
    }


@app.post("/jobs/next")
def next_job(worker: str = "worker"):
    """Give the oldest waiting job to this worker, or 204 No Content when there is nothing to do."""
    with lock:
        _requeue_stale_jobs()
        workers_seen[worker] = time.time()
        row = db.execute("SELECT * FROM jobs WHERE status = 'queued' ORDER BY created LIMIT 1").fetchone()
        if row is None:
            return Response(status_code=204)
        db.execute(
            "UPDATE jobs SET status = 'running', worker = ?,"
            " attempts= attempts+1, message = 'Starting...', updated = ? WHERE id = ?",
            (worker, time.time(), row["id"]),
        )
    return {
        "id": row["id"],
        "text": row["text"],
        "title": row["title"],
        "speakers": json.loads(row["speakers"]),
        "detail_level": row["detail_level"],
        "language": row["language"],
    }


@app.post("/jobs/{job_id}/alive")
def report_alive(job_id: str, worker: str = ""):
    """The worker is still busy with this job, so it must not be given to another worker."""
    with lock:
        row = _get(job_id)
        if _is_current_worker(row, worker):
            db.execute("UPDATE jobs SET updated = ? WHERE id = ? AND status = 'running'", (time.time(), job_id))
    return {"ok": True}


@app.post("/jobs/{job_id}/progress")
def report_progress(job_id: str, progress: Progress, worker: str = ""):
    """A worker reports how far it is."""
    with lock:
        if not _is_current_worker(_get(job_id), worker):
            return {"ok": False}
        db.execute(
            "UPDATE jobs SET progress = ?, message = ?, updated = ? WHERE id = ? AND status = 'running'",
            (progress.fraction, progress.message, time.time(), job_id),
        )
    return {"ok": True}


@app.post("/jobs/{job_id}/result")
def report_result(job_id: str, result: Result, worker: str = ""):
    """A worker delivers the summary; the transcript is deleted."""
    with lock:
        if not _is_current_worker(_get(job_id), worker):
            return {"ok": False}
        # The transcript is not needed any more: remove it right away (privacy).
        db.execute(
            "UPDATE jobs SET status = 'done', progress = 1, message = 'Done', result_title = ?, result_body = ?, "
            "text = NULL, updated = ? WHERE id = ?",
            (result.title, result.body, time.time(), job_id),
        )
    return {"ok": True}


@app.post("/jobs/{job_id}/error")
def report_error(job_id: str, failure: Failure, worker: str = ""):
    """A worker reports a failure; the transcript is deleted."""
    with lock:
        if not _is_current_worker(_get(job_id), worker):
            return {"ok": False}
        db.execute(
            "UPDATE jobs SET status = 'failed', message = 'Failed', error = ?, text = NULL, updated = ? WHERE id = ?",
            (failure.message, time.time(), job_id),
        )
    return {"ok": True}
