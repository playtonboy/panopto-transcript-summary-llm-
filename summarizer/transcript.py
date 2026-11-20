"""Reads a Panopto transcript: removes timestamps and line numbers, finds the title and speakers."""

from dataclasses import dataclass, field
import re
import config

@dataclass
class Transcript:
    """A cleaned transcript with its title and speakers."""
    text: str
    title: str = ""
    speakers: list[str] = field(default_factory=list)

    @property
    def word_count(self) -> int:
        return len(self.text.split())

# Patterns for identifying transcript information

TIMESTAMP_PATTERN = re.compile(
    r"^\s*\d{1,2}:\d{2}(:\d{2})?([.,]\d+)?\s*(-->.*)?$"
)

NUMBER_PATTERN = re.compile(r"^\s*\d+\s*$")

TITLE_PATTERN = re.compile(r"^Title:\s*(.*)$", re.IGNORECASE)

SPEAKER_PATTERN = re.compile(
    r"^((?:Speaker \d+)|(?:[A-Z][\w.'-]*(?: [A-Z][\w.'-]*){0,2})):\s*(.+)$"
)

class TranscriptError(Exception): 
    """A transcript that cannot be used; its message is shown to the user."""
    pass

def parse(raw_text: str) -> Transcript:
    """Clean a raw transcript and return it as a Transcript."""
    title = ""
    speakers = []
    cleaned_lines = []

    for line in raw_text.splitlines():
        line = line.strip()

        if not line:
            continue

        if TIMESTAMP_PATTERN.match(line):
            continue

        if NUMBER_PATTERN.match(line):
            continue

        # Find the lecture title
        title_match=TITLE_PATTERN.match(line)
        if title_match:
            title=title_match.group(1)
            continue

        # Find speaker names
        speaker=None
        speaker_match = SPEAKER_PATTERN.match(line)
        if speaker_match:
            speaker = speaker_match.group(1)
            line = speaker_match.group(2)

            if speaker not in speakers:
                speakers.append(speaker)

        # Keep the spoken words
        cleaned_lines.append((speaker,line))

    # Mark speaker changes when multiple speakers are present
    lines = []
    current = None

    for speaker, line in cleaned_lines:
        if len(speakers) > 1 and speaker and speaker != current:
            line = f"[{speaker}] {line}"
            current = speaker

        lines.append(line)

    # Combine all spoken lines into one text
    text = " ".join(lines)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()


    transcript = Transcript(
        text=text,
        title=title,
        speakers=speakers
    )

    # Reject transcripts that are too short to summarize
    if transcript.word_count < config.MIN_TRANSCRIPT_WORDS:
        raise TranscriptError(
            f"Transcript too short ({transcript.word_count} words)."
        )

    letters = sum(char.isalpha() for char in text)
    meaningful_ratio = letters / len(text) if text else 0

    if meaningful_ratio < 0.5:
        raise TranscriptError(
            "This file does not appear to contain a valid transcript. "
            "Please upload a text file containing spoken language."
        )

    return transcript

