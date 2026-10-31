"""Turns a cleaned transcript into a structured summary (FR7, FR14, FR18, UR4, UR5)."""

import re
from collections.abc import Callable
from dataclasses import dataclass

import config
from summarizer import llm_client, chunking
from summarizer.transcript import Transcript

SYSTEM_PROMPT = (
    "You summarize university lecture transcripts for students. "
    "Only use information that appears in the transcript; never add facts that are not there. "
    "Ignore filler speech, greetings and small talk unless it contains deadlines or tasks."
)

CHUNK_PROMPT = (
    "Below is part {index} of {total} of a lecture transcript. Write concise notes covering every "
    "important concept, definition, example and task mentioned in this part. Copy every assignment, "
    "deadline, reading, test and project requirement word for word.\n\n"
    "TRANSCRIPT PART:\n{chunk}"
)

TOPICS_PROMPT = (
    "List the main topics of the lecture below as a short Markdown bullet list (one '- ' line per topic, "
    "a few words each, in lecture order). Output only the list.\n\n"
    "MATERIAL:\n{material}"
)

# Small models follow a count far better when they number the lines, so we ask for 1..N
# and turn the numbers into bullets afterwards.
SUMMARY_PROMPT = (
    "Write the key insights of the lecture below as a numbered list with exactly {bullets} points, "
    "numbered 1 to {bullets}, in lecture order. Each point is one sentence. "
    "{depth}{speaker_hint}Output only the numbered list.\n\n"
    "MATERIAL:\n{material}"
)

FIX_COUNT_PROMPT = (
    "The numbered list below has {count} points but it must have exactly {bullets}. "
    "Rewrite it with exactly {bullets} points, numbered 1 to {bullets}, by {how}. "
    "Keep the lecture order and do not add facts. Output only the numbered list.\n\n"
    "LIST:\n{points}\n\n"
    "LECTURE:\n{material}"
)

ACTION_ITEMS_PROMPT = (
    "Find everything in the lecture below that students have to do. That includes assignments, "
    "deadlines, readings, quizzes and exams, and requirements for their projects or coursework "
    "(anything they 'must' do or that is graded). Write each one as a Markdown bullet ('- '), "
    "with its date or time if one is given. Output only the list. "
    "If there is nothing, output exactly: None mentioned\n\n"
    "MATERIAL:\n{material}"
)

DEPTH_HINTS = {
    "Short": "Only cover the most important ideas. ",
    "Detailed": "Go into detail: include definitions, examples, answers to student questions and finer points. ",
}

# A very short transcript cannot fill 15 points without the model inventing content,
# so we allow at most one point per this many words.
WORDS_PER_POINT = 30

NUMBERED_LINE = re.compile(r"^\s*\d+[.)]\s+(.*\S)")
BULLET_LINE = re.compile(r"^\s*[-*•]\s+(.*\S)")


@dataclass
class Summary:
    title: str
    body: str

    def as_text(self) -> str:
        return "\n".join([self.title, "", self.body, "", config.AI_DISCLAIMER])  # NFR12


def _list_items(text: str, pattern: re.Pattern) -> list[str]:
    return [m.group(1) for line in text.splitlines() if (m := pattern.match(line))]


def _as_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _summary_points(material: str, bullets: int, detail_level: str, speaker_hint: str) -> list[str]:
    prompt = SUMMARY_PROMPT.format(
        bullets=bullets, depth=DEPTH_HINTS.get(detail_level, ""), speaker_hint=speaker_hint, material=material
    )
    points = _list_items(llm_client.chat(SYSTEM_PROMPT, prompt), NUMBERED_LINE)
    if points and len(points) != bullets:
        how = "splitting points into more specific ones" if len(points) < bullets else "merging related points"
        retry = FIX_COUNT_PROMPT.format(
            count=len(points),
            bullets=bullets,
            how=how,
            points="\n".join(f"{i}. {p}" for i, p in enumerate(points, start=1)),
            material=material,
        )
        fixed = _list_items(llm_client.chat(SYSTEM_PROMPT, retry), NUMBERED_LINE)
        # Keep whichever attempt is closer to the requested length.
        if fixed and abs(len(fixed) - bullets) <= abs(len(points) - bullets):
            points = fixed
    return points[:bullets]


def summarize(
    transcript: Transcript,
    detail_level: str = config.DEFAULT_DETAIL_LEVEL,
    on_progress: Callable[[str, float], None] = lambda message, fraction: None,
) -> Summary:
    if detail_level not in config.DETAIL_LEVELS:
        detail_level = config.DEFAULT_DETAIL_LEVEL
    bullets = min(config.DETAIL_LEVELS[detail_level], max(1, transcript.word_count // WORDS_PER_POINT))
    chunks = chunking.split_into_chunks(transcript.text)
    steps = len(chunks) + 3 if len(chunks) > 1 else 3

    if len(chunks) == 1:
        material = chunks[0]
    else:
        notes = []
        for i, chunk in enumerate(chunks, start=1):
            on_progress(f"Reading part {i} of {len(chunks)}...", (i - 1) / steps)
            notes.append(llm_client.chat(SYSTEM_PROMPT, CHUNK_PROMPT.format(index=i, total=len(chunks), chunk=chunk)))
        material = "\n\n".join(notes)
    done = steps - 3

    speaker_hint = (
        f"The speakers are: {', '.join(transcript.speakers)}. Mention who said what when it matters. "
        if len(transcript.speakers) > 1
        else ""
    )

    on_progress("Finding the main topics...", done / steps)
    topics = _list_items(llm_client.chat(SYSTEM_PROMPT, TOPICS_PROMPT.format(material=material)), BULLET_LINE)

    on_progress("Writing the summary...", (done + 1) / steps)
    points = _summary_points(material, bullets, detail_level, speaker_hint)

    on_progress("Collecting action items...", (done + 2) / steps)
    actions = _list_items(llm_client.chat(SYSTEM_PROMPT, ACTION_ITEMS_PROMPT.format(material=material)), BULLET_LINE)

    body = "\n".join([
        "## Main topics",
        _as_bullets(topics) or "- (no topics found)",
        "",
        "## Summary",
        _as_bullets(points) or "- (no summary generated)",
        "",
        "## Action items",
        _as_bullets(actions) or "- None mentioned",
    ])
    on_progress("Done", 1.0)

    return Summary(title=transcript.title or "Lecture summary", body=body)
