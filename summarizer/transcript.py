from dataclasses import dataclass, field
import re
import config

@dataclass #store transcript information
class Transcript:
    text: str #stores cleaned lecture script
    title: str = ""
    speakers: list[str] = field(default_factory=list) #stores a list of people speaking

    @property
    def word_count(self) -> int: #counts how many words are in the script
        return len(self.text.split())

#patterns for identifying transcript information

TIMESTAMP_PATTERN = re.compile(
    r"^\s*\d{1,2}:\d{2}(:\d{2})?([.,]\d+)?\s*(-->.*)?$"
)

NUMBER_PATTERN = re.compile(r"^\s*\d+\s*$")

TITLE_PATTERN = re.compile(r"^Title:\s*(.*)$", re.IGNORECASE)

SPEAKER_PATTERN = re.compile(r"^([A-Z][\w.'-]*(?: [A-Z][\w.'-]*){0,2}):\s*(.+)$")

class TranscriptError(Exception): #this is custom error for transcripts that fail validation (if script is too short)
    pass

def parse(raw_text: str) -> Transcript: #returns original transcript as object
    title = "" #store information that is found
    speakers = []
    cleaned_lines = [] #list to collect actual spoken words

    for line in raw_text.splitlines():
        line = line.strip() #remove extra spaces from begin and end

        if not line:
            continue

        if TIMESTAMP_PATTERN.match(line):
            continue

        if NUMBER_PATTERN.match(line):
            continue

        #find the lecture title
        title_match=TITLE_PATTERN.match(line)
        if title_match:
            title=title_match.group(1)
            continue

        #find speaker names
        speaker_match = SPEAKER_PATTERN.match(line)
        if speaker_match:
            speaker = speaker_match.group(1)
            line = speaker_match.group(2)

            if speaker not in speakers:
                speakers.append(speaker)

        # Keep the spoken words
        cleaned_lines.append(line)

    #combines all spoken lines into one text
    text = " ".join(cleaned_lines)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()


    transcript = Transcript(
        text=text,
        title=title,
        speakers=speakers
    )

    #reject transcripts that are too short to summarize
    if transcript.word_count < config.MIN_TRANSCRIPT_WORDS:
        raise TranscriptError(
            f"Transcript too short ({transcript.word_count} words)."
        )

    return transcript

