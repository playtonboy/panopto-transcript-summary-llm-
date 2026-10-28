"""Integration tests: several parts of the app working together, with a fake LM Studio instead of the real one."""

import socket
from pathlib import Path

import pytest

import config
from fake_lmstudio import start_fake_server
from summarizer import export, llm_client
from summarizer.summarize import summarize
from summarizer.transcript import parse
from summarizer.upload_validation import decode, validate_upload

SAMPLE_FILE = Path(__file__).parent / "data" / "sample_transcript.txt"
SAMPLE = SAMPLE_FILE.read_text(encoding="utf-8")


@pytest.fixture
def fake_server(monkeypatch):
    """Start a fake LM Studio and point the app at it. Call it as fake_server() or fake_server(delay_s=2)."""
    servers = []

    def start(**options):
        server, url = start_fake_server(**options)
        servers.append(server)
        monkeypatch.setattr(config, "LMSTUDIO_BASE_URL", url)
        return server

    yield start
    for server in servers:  # runs after the test: stop every server it started
        server.shutdown()


def test_full_run_from_upload_to_download(fake_server):
    fake_server()
    data = SAMPLE_FILE.read_bytes()

    validate_upload(SAMPLE_FILE.name, len(data))  # 1. the upload checks
    transcript = parse(decode(data))              # 2. reading and cleaning the file
    summary = summarize(transcript, detail_level="Short")  # 3. the three calls to the model
    text = export.to_txt(summary).decode("utf-8")          # 4. the download

    assert summary.title == "Software Engineering Lecture 3"
    assert "## Main topics" in summary.body and "- Software testing" in summary.body
    assert "- Fake point 1." in summary.body
    assert "- Hand in Task 5 on 6 November" in summary.body
    assert text.startswith("Software Engineering Lecture 3")


def test_server_down_gives_a_friendly_error(monkeypatch):
    with socket.socket() as s:  # ask the computer for a free port, so nothing is listening on it
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    monkeypatch.setattr(config, "LMSTUDIO_BASE_URL", f"http://127.0.0.1:{port}/v1")

    assert llm_client.is_server_running() is False
    with pytest.raises(llm_client.LLMError, match="Could not reach LM Studio"):
        summarize(parse(SAMPLE))


def test_slow_model_gives_a_timeout_error(fake_server, monkeypatch):
    fake_server(delay_s=2)
    monkeypatch.setattr(config, "REQUEST_TIMEOUT_S", 0.5)  # give up after half a second

    with pytest.raises(llm_client.LLMError, match="took too long"):
        summarize(parse(SAMPLE))


def test_server_error_gives_a_friendly_error(fake_server):
    fake_server(status=500)

    assert llm_client.is_server_running() is True  # the server is up...
    with pytest.raises(llm_client.LLMError, match="returned 500"):  # ...but the model call fails
        summarize(parse(SAMPLE))