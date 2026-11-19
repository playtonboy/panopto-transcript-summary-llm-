"""The Streamlit interface sends work to the orchestrator and never calls the AI itself (Task 6, SCRUM-52)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from interface import client
from summarizer.summarize import Summary

PASTED = "Good morning everyone. Today we talk about unit tests and integration tests. " * 5


def run_with_fake_orchestrator(monkeypatch, wait_for_summary):
    sent = []
    monkeypatch.setattr(client, "health", lambda url=None:{"status":"ok","workers":1})
    monkeypatch.setattr(client, "submit", lambda transcript, **options: sent.append((transcript, options)) or "job-1")
    monkeypatch.setattr(client, "wait_for_summary", wait_for_summary)
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()
    at.text_area[0].input(PASTED)
    at.button[0].click().run()
    return at, sent


def test_generate_sends_a_job_and_shows_the_result(monkeypatch):
    def finished(job_id, on_progress, url=None):
        on_progress("Writing the summary...", 0.5)
        return Summary(title="Lecture summary", body="## Summary\n- Unit tests check one function.")

    at, sent = run_with_fake_orchestrator(monkeypatch, finished)
    assert not at.exception
    transcript, options = sent[0]
    assert transcript.text.startswith("Good morning everyone")
    assert options == {"detail_level": "Medium", "language": "English","url":"http://localhost:8000",}
    assert any("Unit tests check one function." in m.value for m in at.markdown)


def test_a_failed_job_shows_its_message(monkeypatch):
    def failed(job_id, on_progress,url=None):
        raise client.JobFailed("Could not reach LM Studio.")

    at, _ = run_with_fake_orchestrator(monkeypatch, failed)
    assert not at.exception
    assert at.error[0].value == "Could not reach LM Studio."


def test_interface_never_calls_the_ai_directly():
    code = (Path(__file__).parent.parent / "app.py").read_text(encoding="utf-8")
    assert "llm_client" not in code
    assert "summarize(" not in code


def test_settings_panel_sends_jobs_to_the_chosen_local_address(monkeypatch):
    seen = []

    monkeypatch.setattr(
        client,
        "health",
        lambda url=None: seen.append(url) or {"status": "ok", "workers": 1},
    )

    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()

    at.sidebar.text_input[0].input("http://localhost:8001").run()

    assert seen[-1] == "http://localhost:8001"
    assert not at.sidebar.error


def test_settings_panel_refuses_addresses_on_other_computers(monkeypatch):
    seen = []

    monkeypatch.setattr(
        client,
        "health",
        lambda url=None: seen.append(url) or {"status": "ok", "workers": 1},
    )

    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()

    at.sidebar.text_input[0].input("http://example.com:8000").run()

    assert "Only addresses on this computer" in at.sidebar.error[0].value
    assert seen[-1] == "http://localhost:8000"


def test_regenerate_uses_the_same_transcript_with_the_new_settings(monkeypatch):
    bodies = iter(["## Summary\n- First version.", "## Summary\n- Second version."])

    def finished(job_id, on_progress, url=None):
        return Summary(title="Lecture summary", body=next(bodies))

    at, sent = run_with_fake_orchestrator(monkeypatch, finished)
    assert not at.button[1].disabled
    at.radio[0].set_value("Short")
    at.button[1].click().run()

    assert not at.exception
    assert len(sent) == 2
    assert sent[1][0].text == sent[0][0].text
    assert sent[1][1]["detail_level"] == "Short"
    assert any("Second version." in m.value for m in at.markdown)
    assert "(1)" in at.expander[0].label
    assert any("First version." in m.value for m in at.expander[0].markdown)


def test_regenerate_is_disabled_before_the_first_summary(monkeypatch):
    monkeypatch.setattr(client, "health", lambda url=None: {"status": "ok", "workers": 1})
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()
    assert at.button[1].disabled


def test_history_keeps_only_the_last_five_summaries(monkeypatch):
    count = iter(range(1, 100))

    def finished(job_id, on_progress, url=None):
        return Summary(title="Lecture summary", body=f"- Version {next(count)}.")

    at, _ = run_with_fake_orchestrator(monkeypatch, finished)
    for _ in range(6):
        at.button[1].click().run()
    assert len(at.session_state["history"]) == 5
    assert "(4)" in at.expander[0].label


class FakeUpload:
    def __init__(self, name, data):
        self.name, self.size, self._data = name, len(data), data

    def getvalue(self):
        return self._data


def run_with_upload(monkeypatch, upload):
    import streamlit

    sent = []
    monkeypatch.setattr(client, "health", lambda url=None: {"status": "ok", "workers": 1})
    monkeypatch.setattr(client, "submit", lambda transcript, **options: sent.append(transcript) or "job-1")
    monkeypatch.setattr(streamlit, "file_uploader", lambda *args, **kwargs: upload)
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()
    at.button[0].click().run()
    return at, sent


def test_a_wrong_file_type_is_shown_to_the_user(monkeypatch):
    at, sent = run_with_upload(monkeypatch, FakeUpload("slides.pptx", b"not a transcript"))
    assert not at.exception
    assert "Unsupported file type" in at.error[0].value
    assert sent == []


def test_a_pdf_renamed_to_txt_is_shown_to_the_user(monkeypatch):
    at, sent = run_with_upload(monkeypatch, FakeUpload("lecture.txt", b"%PDF-1.7 binary"))
    assert "appears to be a PDF" in at.error[0].value
    assert sent == []


def test_an_empty_file_is_shown_to_the_user(monkeypatch):
    at, sent = run_with_upload(monkeypatch, FakeUpload("lecture.txt", b""))
    assert "empty" in at.error[0].value
    assert sent == []


def test_a_too_short_transcript_is_shown_to_the_user(monkeypatch):
    at, sent = run_with_upload(monkeypatch, FakeUpload("lecture.txt", b"Hello everyone."))
    assert at.error[0].value.startswith("Transcript too short")
    assert sent == []


def test_generate_without_a_transcript_asks_for_one(monkeypatch):
    at, sent = run_with_upload(monkeypatch, None)
    assert at.error[0].value == "Please upload a transcript or paste its text first."
    assert sent == []
