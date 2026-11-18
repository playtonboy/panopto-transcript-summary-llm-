"""Exports a summary as .txt, .docx or .pdf (FR4, UR8, NFR7). Files are built in memory only, never saved (NFR3)."""

import io

from docx import Document
from fpdf import FPDF

import config


def to_txt(summary) -> bytes:
    return summary.as_text().encode("utf-8")


def to_docx(summary) -> bytes:
    doc = Document()
    doc.add_heading(summary.title, level=1)
    for line in summary.body.splitlines():
        text = line.strip().replace("**", "")
        if not text:
            continue
        if text.startswith("#"):
            doc.add_heading(text.lstrip("#").strip(), level=2)
        elif text.startswith(("- ", "* ")):
            doc.add_paragraph(text[2:], style="List Bullet")
        else:
            doc.add_paragraph(text)
    doc.add_paragraph().add_run(config.AI_DISCLAIMER).italic = True  # NFR12

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()

_PLAIN = {
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "–": "-",
    "—": "-",
    "…": "...",
    "•": "-",
}


def _latin1(text: str) -> str:
    for fancy, plain in _PLAIN.items():
        text = text.replace(fancy, plain)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def to_pdf(summary) -> bytes:
    """The summary as a PDF file, with headings, bullets and the AI disclaimer."""
    pdf = FPDF()
    pdf.set_compression(False)
    pdf.set_margins(20, 20)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.multi_cell(0, 9, _latin1(summary.title), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    for line in summary.body.splitlines():
        text = _latin1(line.strip().replace("**", ""))
        if not text:
            continue
        if text.startswith("#"):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(0, 7, text.lstrip("#").strip(), new_x="LMARGIN", new_y="NEXT")
        elif text.startswith(("- ", "* ")):
            pdf.set_font("Helvetica", "", 11)
            pdf.set_x(24)
            pdf.multi_cell(0, 6, "-  " + text[2:], new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 5, _latin1(config.AI_DISCLAIMER), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())