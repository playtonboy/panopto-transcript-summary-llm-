"""Unit tests for summarizer/export.py (the .txt and .docx downloads)."""

import io

from docx import Document

from summarizer.export import to_docx, to_txt
from summarizer.summarize import Summary

SUMMARY = Summary(
    title="Lecture 3",
    body="## Main topics\n- Unit testing\n- **pytest** basics\nA short closing sentence.",
    source_url="",
)


def test_to_txt_contains_title_and_body():
    text = to_txt(SUMMARY).decode("utf-8")
    assert text.startswith("Lecture 3")
    assert "- Unit testing" in text


def test_to_docx_is_a_real_word_file_with_the_right_content():
    data = to_docx(SUMMARY)
    doc = Document(io.BytesIO(data)) 
    paragraphs = [p.text for p in doc.paragraphs]

    assert paragraphs[0] == "Lecture 3"
    assert "Main topics" in paragraphs
    assert "pytest basics" in paragraphs  
    assert doc.paragraphs[2].style.name == "List Bullet"