"""Tests for the prompt changes of SCRUM-18 (fewer, real topics; points spread over the lecture; real tasks only)."""

from pathlib import Path

import config
from summarizer import llm_client
from summarizer.summarize import MAX_TOPICS, summarize
from summarizer.transcript import parse

SAMPLE = (Path(__file__).parent / "data" / "sample_transcript.txt").read_text(encoding="utf-8")
TOO_MANY_TOPICS = "\n".join(f"- Topic {i}" for i in range(1, 13))  # 12 topics


def fake_model(monkeypatch, topics_answer="- Unit tests\n- Integration tests"):
    """Replace the model; remember every prompt and answer like the real prompts expect."""
    prompts = []

    def chat(system_prompt, user_prompt):
        prompts.append(user_prompt)
        if user_prompt.startswith("List the main topics"):
            return topics_answer
        if user_prompt.startswith("Find everything"):
            return "- Hand in Task 5 on 6 November"
        if "numbered list with exactly" in user_prompt:
            return "\n".join(f"{i}. Point {i}." for i in range(1, 6))
        return "Some notes.\nStudent tasks: none"

    monkeypatch.setattr(llm_client, "chat", chat)
    return prompts


def test_topics_are_capped_even_if_the_model_lists_too_many(monkeypatch):
    fake_model(monkeypatch, topics_answer=TOO_MANY_TOPICS)
    body = summarize(parse(SAMPLE), detail_level="Short").body
    topics = body.split("## Main topics", 1)[1].split("## Summary", 1)[0]
    assert topics.count("\n- ") == MAX_TOPICS


def test_summary_prompt_names_the_topics_and_asks_to_cover_the_whole_lecture(monkeypatch):
    prompts = fake_model(monkeypatch)
    summarize(parse(SAMPLE), detail_level="Short")
    summary_prompt = next(p for p in prompts if "numbered list with exactly" in p)
    assert "Unit tests; Integration tests" in summary_prompt
    assert "Give every main topic at least one point" in summary_prompt
    assert "beginning, middle and end" in summary_prompt


def test_action_items_prompt_only_asks_for_the_students_own_tasks(monkeypatch):
    prompts = fake_model(monkeypatch)
    summarize(parse(SAMPLE), detail_level="Short")
    action_prompt = next(p for p in prompts if p.startswith("Find everything"))
    assert "students of this course" in action_prompt
    assert "Do NOT list what AI systems" in action_prompt
    assert "'I would like you to read...'" in action_prompt  # informal requests count as tasks too
    assert "Understanding, learning or knowing a topic of the lecture is not a task" in action_prompt


def test_long_lecture_notes_keep_student_tasks_separate(monkeypatch):
    prompts = fake_model(monkeypatch)
    monkeypatch.setattr(config, "CHUNK_TOKENS", 50)  # force several parts
    monkeypatch.setattr(config, "CHUNK_OVERLAP_TOKENS", 5)
    summarize(parse(SAMPLE * 5), detail_level="Short")
    chunk_prompts = [p for p in prompts if p.startswith("Below is part")]
    assert len(chunk_prompts) > 1
    assert all("Student tasks:" in p for p in chunk_prompts)
    assert all("'I would like you to read...'" in p for p in chunk_prompts)  # informal tasks are kept in the notes


def test_no_topics_found_still_gives_a_valid_summary_prompt(monkeypatch):
    prompts = fake_model(monkeypatch, topics_answer="")
    summarize(parse(SAMPLE), detail_level="Short")
    summary_prompt = next(p for p in prompts if "numbered list with exactly" in p)
    assert "The main topics are: see the material." in summary_prompt
