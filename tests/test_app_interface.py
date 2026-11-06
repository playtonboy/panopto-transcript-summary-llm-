"""The Streamlit interface sends work to the orchestrator and never calls the AI itself (Task 6, SCRUM-52)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from interface import client
from summarizer.summarize import Summary

PASTED = "Good morning everyone. Today we talk about unit tests and integration tests. " * 5


def run_with_fake_orchestrator(monkeypatch, wait_for_summary):
    sent = []
    monkeypatch.setattr(client, "is_running", lambda: True)
    monkeypatch.setattr(client, "submit", lambda transcript, **options: sent.append((transcript, options)) or "job-1")
    monkeypatch.setattr(client, "wait_for_summary", wait_for_summary)
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()
    at.text_area[0].input(PASTED)
    at.button[0].click().run()
    return at, sent


def test_generate_sends_a_job_and_shows_the_result(monkeypatch):
    def finished(job_id, on_progress):
        on_progress("Writing the summary...", 0.5)
        return Summary(title="Lecture summary", body="## Summary\n- Unit tests check one function.")

    at, sent = run_with_fake_orchestrator(monkeypatch, finished)
    assert not at.exception
    transcript, options = sent[0]
    assert transcript.text.startswith("Good morning everyone")
    assert options == {"detail_level": "Medium", "language": "English"}
    assert any("Unit tests check one function." in m.value for m in at.markdown)


def test_a_failed_job_shows_its_message(monkeypatch):
    def failed(job_id, on_progress):
        raise client.JobFailed("Could not reach LM Studio.")

    at, _ = run_with_fake_orchestrator(monkeypatch, failed)
    assert not at.exception
    assert at.error[0].value == "Could not reach LM Studio."


def test_interface_never_calls_the_ai_directly():
    code = (Path(__file__).parent.parent / "app.py").read_text(encoding="utf-8")
    assert "llm_client" not in code
    assert "summarize(" not in code