"""Unit tests for summarizer/upload_validation.py (checking uploaded files)."""

import pytest

import config
from summarizer.transcript import TranscriptError
from summarizer.upload_validation import decode, validate_upload


def test_validate_upload_accepts_a_normal_txt_file():
    validate_upload("lecture3.txt", 2_000)  # no error means the file is accepted


def test_validate_upload_rejects_other_file_types():
    with pytest.raises(TranscriptError, match="Unsupported file type"):
        validate_upload("lecture3.pdf", 2_000)


def test_validate_upload_rejects_an_empty_file():
    with pytest.raises(TranscriptError, match="empty"):
        validate_upload("lecture3.txt", 0)


def test_validate_upload_rejects_a_file_that_is_too_big():
    too_big = config.MAX_UPLOAD_MB * 1024 * 1024 + 1
    with pytest.raises(TranscriptError, match="larger than"):
        validate_upload("lecture3.txt", too_big)


def test_decode_reads_utf8_text():
    assert decode("Café lecture".encode("utf-8")) == "Café lecture"


def test_decode_rejects_a_pdf_renamed_to_txt():
    with pytest.raises(TranscriptError, match="PDF"):
        decode(b"%PDF-1.7 fake pdf content")