"""Unit tests for summarizer/chunking.py (splitting long transcripts)."""

import config
from summarizer.chunking import split_into_chunks


def test_short_text_stays_in_one_chunk():
    text = "This is a short lecture. It fits easily."
    assert split_into_chunks(text) == [text]


def test_long_text_is_split_into_chunks_that_fit(monkeypatch):
    # Make the chunk size tiny so a short test text counts as "long".
    monkeypatch.setattr(config, "CHUNK_TOKENS", 25) 
    monkeypatch.setattr(config, "CHUNK_OVERLAP_TOKENS", 5)   
    max_chars = 25 * config.CHARS_PER_TOKEN

    text = " ".join(f"Sentence number {i} is here." for i in range(30))
    chunks = split_into_chunks(text)

    assert len(chunks) > 1
    assert all(len(chunk) <= max_chars for chunk in chunks)
    assert chunks[0].startswith("Sentence number 0")
    assert chunks[-1].endswith("Sentence number 29 is here.")


def test_each_chunk_repeats_the_end_of_the_previous_one(monkeypatch):
    monkeypatch.setattr(config, "CHUNK_TOKENS", 25)
    monkeypatch.setattr(config, "CHUNK_OVERLAP_TOKENS", 5)
    overlap_chars = 5 * config.CHARS_PER_TOKEN

    text = " ".join(f"Sentence number {i} is here." for i in range(30))
    chunks = split_into_chunks(text)

    for previous, current in zip(chunks, chunks[1:]):
        assert current.startswith(previous[-overlap_chars:])