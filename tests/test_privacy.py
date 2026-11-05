"""Privacy checks (SCRUM-29, NFR3, NFR4, NFR10): nothing is written to disk and nothing leaves the computer."""

import builtins
import io
from pathlib import Path
from urllib.parse import urlparse

import pytest
import urllib3.util.connection

import config
from fake_lmstudio import start_fake_server
from summarizer import export
from summarizer.summarize import summarize
from summarizer.transcript import parse
from summarizer.upload_validation import decode, validate_upload

ROOT = Path(__file__).parent.parent
SAMPLE_FILE = Path(__file__).parent / "data" / "sample_transcript.txt"
SAMPLE_FILE_NL = Path(__file__).parent / "data" / "sample_transcript_nl.txt"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def test_lm_studio_address_is_this_computer():
    assert urlparse(config.LMSTUDIO_BASE_URL).hostname in LOCAL_HOSTS


def test_streamlit_sends_no_usage_stats_and_is_only_reachable_locally():
    tomllib = pytest.importorskip("tomllib")  # Python 3.11+; skipped on older Python
    settings = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    assert settings["browser"]["gatherUsageStats"] is False
    assert settings["server"]["address"] == "localhost"


@pytest.fixture
def watch(monkeypatch, tmp_path):
    """Record every network connection and every file opened for writing while a test runs."""
    seen = {"hosts": [], "written": []}

    real_connect = urllib3.util.connection.create_connection

    def connect(address, *args, **kwargs):
        seen["hosts"].append(address[0])
        return real_connect(address, *args, **kwargs)

    real_open = builtins.open

    def open_(file, mode="r", *args, **kwargs):
        if any(flag in mode for flag in "wax+"):
            seen["written"].append(str(file))
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(urllib3.util.connection, "create_connection", connect)
    monkeypatch.setattr(builtins, "open", open_)
    monkeypatch.setattr(io, "open", open_)
    monkeypatch.chdir(tmp_path)  # any stray file would land here
    return seen


@pytest.mark.parametrize(
    "sample, language",
    [(SAMPLE_FILE, "English"), (SAMPLE_FILE_NL, "Dutch"), (SAMPLE_FILE, "German")],
)
def test_full_run_writes_no_files_and_only_talks_to_localhost(watch, monkeypatch, tmp_path, sample, language):
    server, url = start_fake_server()
    monkeypatch.setattr(config, "LMSTUDIO_BASE_URL", url)
    try:
        data = sample.read_bytes()
        validate_upload(sample.name, len(data))
        transcript = parse(decode(data))
        summary = summarize(transcript, detail_level="Short", language=language)
        export.to_txt(summary)
        export.to_docx(summary)
    finally:
        server.shutdown()

    assert watch["hosts"], "the test should have called the (fake) model"
    assert set(watch["hosts"]) <= LOCAL_HOSTS
    assert watch["written"] == []
    assert list(tmp_path.iterdir()) == []


def test_summary_does_not_keep_the_transcript_text(monkeypatch):
    """Only the summary is kept between clicks (st.session_state); the transcript itself is not stored in it."""
    transcript = parse(SAMPLE_FILE.read_text(encoding="utf-8"))
    server, url = start_fake_server()
    monkeypatch.setattr(config, "LMSTUDIO_BASE_URL", url)
    try:
        summary = summarize(transcript, detail_level="Short")
    finally:
        server.shutdown()

    assert transcript.text not in summary.as_text()
    assert "unit test checks one small piece of code" not in summary.as_text()
