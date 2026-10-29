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