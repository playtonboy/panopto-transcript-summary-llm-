"""Loading, validating and cleaning Panopto transcripts (FR1, FR2, FR5, FR16, UR9)."""

import re
from dataclasses import dataclass, field

import config


class TranscriptError(ValueError):
    """Raised when a transcript cannot be used. The message is shown to the user (FR8)."""


@dataclass
class Transcript:
    text: str
    title: str | None = None
    url: str | None = None
    speakers: list[str] = field(default_factory=list)

    @property
    def word_count(self) -> int:
        return len(self.text.split())


# Caption-style exports contain sequence numbers and timestamps such as
# "00:01:23,450 --> 00:01:27,000" or "[00:01:23]". They carry no meaning for a summary.
_TIMESTAMP_LINE = re.compile(r"^\s*\d{1,2}:\d{2}(:\d{2})?([.,]\d+)?\s*(-->\s*\d{1,2}:\d{2}(:\d{2})?([.,]\d+)?)?\s*$")
_INLINE_TIMESTAMP = re.compile(r"\[?\(?\b\d{1,2}:\d{2}(:\d{2})?([.,]\d+)?\b\)?\]?")
_SEQUENCE_LINE = re.compile(r"^\s*\d+\s*$")
_SPEAKER_LABEL = re.compile(r"^\s*([A-Z][\w.\- ]{0,40}):\s+\S")
_URL = re.compile(r"https?://\S*panopto\S*", re.IGNORECASE)
_TITLE = re.compile(r"^\s*(title|lecture|session)\s*:\s*(.+)$", re.IGNORECASE)


def validate_upload(filename: str, size_bytes: int) -> None:
    """Check the file before reading it (FR5)."""
    if not filename.lower().endswith(config.ALLOWED_EXTENSIONS):
        raise TranscriptError(
            f"Unsupported file type. Please upload a {', '.join(config.ALLOWED_EXTENSIONS)} transcript."
        )
    if size_bytes == 0:
        raise TranscriptError("The uploaded file is empty.")
    if size_bytes > config.MAX_UPLOAD_MB * 1024 * 1024:
        raise TranscriptError(f"The file is larger than {config.MAX_UPLOAD_MB} MB.")


def decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise TranscriptError("Could not read the file. Please save it as UTF-8 text.")


def parse(raw_text: str) -> Transcript:
    """Turn a raw Panopto export (or pasted text) into clean prose plus metadata."""
    title = url = None
    speakers: list[str] = []
    lines: list[str] = []

    for line in raw_text.splitlines():
        if not line.strip() or _TIMESTAMP_LINE.match(line) or _SEQUENCE_LINE.match(line):
            continue
        if url is None and (m := _URL.search(line)):
            url = m.group(0)
            if line.strip() == url:
                continue
        if title is None and (m := _TITLE.match(line)):
            title = m.group(2).strip()
            continue
        if (m := _SPEAKER_LABEL.match(line)) and m.group(1) not in speakers:
            speakers.append(m.group(1))
        lines.append(_INLINE_TIMESTAMP.sub("", line).strip())

    text = re.sub(r"[ \t]+", " ", "\n".join(lines)).strip()
    transcript = Transcript(text=text, title=title, url=url, speakers=speakers)

    if transcript.word_count < config.MIN_TRANSCRIPT_WORDS:
        raise TranscriptError(
            f"Transcript too short ({transcript.word_count} words). "
            f"At least {config.MIN_TRANSCRIPT_WORDS} words are needed for a useful summary."
        )
    return transcript
