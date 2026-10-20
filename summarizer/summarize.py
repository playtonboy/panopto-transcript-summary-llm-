"""Summarization pipeline (FR7, FR10, FR14, FR16, FR18, UR4, UR5).

Long transcripts use map-reduce: each chunk is summarized into notes first, then all
notes are combined into the final summary. Short transcripts go straight to the final step.
"""

from collections.abc import Callable
from dataclasses import dataclass

import config
from summarizer import chunking, llm_client
from summarizer.transcript import Transcript

SYSTEM_PROMPT = (
    "You summarize university lecture transcripts for students. "
    "Only use information that appears in the transcript; never add facts that are not there. "
    "Ignore filler speech, greetings and administrative small talk unless it contains deadlines or tasks."
)

CHUNK_PROMPT = (
    "Below is part {index} of {total} of a lecture transcript. Write concise notes covering every "
    "important concept, definition, example, decision and task mentioned in this part.\n\n"
    "TRANSCRIPT PART:\n{chunk}"
)

FINAL_PROMPT = (
    "Using the material below, write a lecture summary in {language}.\n"
    "Use exactly this Markdown structure:\n"
    "## Main topics\n- a short list of the main topics discussed\n"
    "## Summary\n- about {bullets} bullet points with the key insights, in lecture order\n"
    "## Action items\n- tasks, deadlines or readings mentioned (write 'None mentioned' if there are none)\n"
    "{speaker_hint}\n"
    "MATERIAL:\n{material}"
)


@dataclass
class Summary:
    title: str
    body: str
    source_url: str | None
    disclaimer: str = config.AI_DISCLAIMER

    def as_text(self) -> str:
        parts = [self.title, "", self.body, ""]
        if self.source_url:
            parts.append(f"Original lecture: {self.source_url}")
        parts.append(self.disclaimer)
        return "\n".join(parts)


def summarize(
    transcript: Transcript,
    detail_level: str = config.DEFAULT_DETAIL_LEVEL,
    language: str = config.DEFAULT_OUTPUT_LANGUAGE,
    title: str | None = None,
    on_progress: Callable[[str, float], None] = lambda message, fraction: None,
) -> Summary:
    bullets = config.DETAIL_LEVELS.get(detail_level, config.DETAIL_LEVELS[config.DEFAULT_DETAIL_LEVEL])
    chunks = chunking.split_into_chunks(transcript.text)

    if len(chunks) == 1:
        material = chunks[0]
    else:
        notes = []
        for i, chunk in enumerate(chunks, start=1):
            on_progress(f"Reading part {i} of {len(chunks)}...", (i - 1) / (len(chunks) + 1))
            notes.append(llm_client.chat(SYSTEM_PROMPT, CHUNK_PROMPT.format(index=i, total=len(chunks), chunk=chunk)))
        material = "\n\n".join(notes)

    on_progress("Writing the summary...", len(chunks) / (len(chunks) + 1))
    speaker_hint = (
        f"The transcript has these speakers: {', '.join(transcript.speakers)}. "
        "Mention who said what when it matters.\n"
        if transcript.speakers
        else ""
    )
    body = llm_client.chat(
        SYSTEM_PROMPT,
        FINAL_PROMPT.format(language=language, bullets=bullets, speaker_hint=speaker_hint, material=material),
    )
    on_progress("Done", 1.0)

    return Summary(
        title=title or transcript.title or "Lecture summary",
        body=body,
        source_url=transcript.url,
    )
