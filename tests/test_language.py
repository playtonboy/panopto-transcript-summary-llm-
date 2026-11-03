"""The chosen output language reaches every request to the model (SCRUM-43)."""

from pathlib import Path

from summarizer import llm_client
from summarizer.summarize import summarize
from summarizer.transcript import parse

SAMPLE = (Path(__file__).parent / "data" / "sample_transcript.txt").read_text(encoding="utf-8")


def record_system_prompts(monkeypatch):
    """Replace the model with a stand-in that remembers every system prompt it was sent."""
    seen = []

    def fake_chat(system_prompt, user_prompt):
        seen.append(system_prompt)
        return "1. A point.\n- A topic"

    monkeypatch.setattr(llm_client, "chat", fake_chat)
    return seen


def test_chosen_language_is_in_every_request(monkeypatch):
    seen = record_system_prompts(monkeypatch)
    summarize(parse(SAMPLE), language="Dutch")
    assert len(seen) == 3  # topics, summary points, action items
    assert all("Always write your answer in Dutch" in prompt for prompt in seen)


def test_unknown_language_falls_back_to_english(monkeypatch):
    seen = record_system_prompts(monkeypatch)
    summarize(parse(SAMPLE), language="Klingon")
    assert all("Always write your answer in English" in prompt for prompt in seen)

def test_dutch_transcript_is_parsed_and_the_model_is_told_it_may_be_dutch(monkeypatch):
    dutch = (Path(__file__).parent / "data" / "sample_transcript_nl.txt").read_text(encoding="utf-8")
    transcript = parse(dutch)
    assert "één klein stukje code" in transcript.text  # accented letters survive
    assert "-->" not in transcript.text

    seen = record_system_prompts(monkeypatch)
    summarize(transcript, language="English")
    assert all("can be in any language" in prompt for prompt in seen)