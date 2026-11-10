"""Unit tests for summarizer/transcript.py (the Panopto parser)."""

from pathlib import Path

import pytest

from summarizer.transcript import TranscriptError, parse

SAMPLE = (Path(__file__).parent / "data" / "sample_transcript.txt").read_text(encoding="utf-8")


def test_parse_removes_timestamps_and_line_numbers():
    transcript = parse(SAMPLE)
    assert "-->" not in transcript.text
    assert "00:00" not in transcript.text
    assert not transcript.text.startswith("1 ")


def test_parse_keeps_the_spoken_words():
    transcript = parse(SAMPLE)
    assert "today we talk about unit testing" in transcript.text
    assert "we run all of them automatically with pytest" in transcript.text


def test_parse_finds_speakers_once_each_in_order():
    transcript = parse(SAMPLE)
    assert transcript.speakers == ["Alice Smith", "Bob"]
    assert "Alice Smith:" not in transcript.text


def test_parse_reads_the_title_line():
    transcript = parse(SAMPLE)
    assert transcript.title == "Software Engineering Lecture 3"
    assert "Title:" not in transcript.text


def test_parse_rejects_a_transcript_that_is_too_short():
    with pytest.raises(TranscriptError):
        parse("00:00:01.000 --> 00:00:02.000\nHello everyone.")

def test_parse_rejects_numbers_and_symbols():
    invalid_text = "12345 !!! @@@ 67890 ### " * 10

    with pytest.raises(TranscriptError, match="valid transcript"):
        parse(invalid_text)


def test_parse_accepts_normal_spoken_language():
    valid_text = (
        "Today we are learning about software engineering "
        "and how to build reliable systems. "
    ) * 5

    transcript = parse(valid_text)
    assert transcript.word_count == 65

def test_parse_marks_who_is_speaking_when_there_are_several_speakers():
    transcript = parse(SAMPLE)
    assert transcript.text.startswith("[Alice Smith] Good morning everyone")
    assert "[Bob] Does that mean" in transcript.text
    assert transcript.text.count("[Alice Smith]") == 2


def test_parse_adds_no_speaker_marks_for_a_single_lecturer():
    one_speaker = SAMPLE.replace("Bob:", "Alice Smith:")
    transcript = parse(one_speaker)
    assert transcript.speakers == ["Alice Smith"]
    assert "[" not in transcript.text


def test_parse_understands_panopto_numbered_speakers():
    numbered = SAMPLE.replace("Alice Smith:", "Speaker 1:").replace("Bob:", "Speaker 2:")
    assert parse(numbered).speakers == ["Speaker 1", "Speaker 2"]

def test_parse_does_not_confuse_tasks_with_speakers():
    text = (
        "Alice: Today we are discussing software engineering and programming. "
        "We will work through several examples during this lecture.\n"
        "Task 5: Complete the assignment and explain your solution.\n"
        "Exercise 4: Write a function that processes the input data.\n"
        "Bob: Can you explain how we should approach the assignment?"
    )

    transcript = parse(text)

    assert transcript.speakers == ["Alice", "Bob"]
    assert "Task 5:" in transcript.text
    assert "Exercise 4:" in transcript.text