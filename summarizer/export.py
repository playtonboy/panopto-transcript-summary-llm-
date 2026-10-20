"""Exporting summaries as .txt and .docx (FR4, UR8, NFR7). Files are built in memory only (NFR3)."""

import io

from docx import Document

from summarizer.summarize import Summary


def to_txt(summary: Summary) -> bytes:
    return summary.as_text().encode("utf-8")


def to_docx(summary: Summary) -> bytes:
    doc = Document()
    doc.add_heading(summary.title, level=1)
    for line in summary.body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            doc.add_heading(stripped.lstrip("#").strip(), level=2)
        elif stripped.startswith(("- ", "* ")):
            doc.add_paragraph(stripped[2:], style="List Bullet")
        else:
            doc.add_paragraph(stripped)
    if summary.source_url:
        doc.add_paragraph(f"Original lecture: {summary.source_url}")
    doc.add_paragraph().add_run(summary.disclaimer).italic = True

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
