"""Splitting long transcripts so nothing is silently cut off (FR11, UR3, NFR8)."""

import config


def estimate_tokens(text: str) -> int:
    return len(text) // config.CHARS_PER_TOKEN + 1


def split_into_chunks(text: str) -> list[str]:
    """Split on sentence boundaries into chunks of about CHUNK_TOKENS, with a small overlap."""
    max_chars = config.CHUNK_TOKENS * config.CHARS_PER_TOKEN
    overlap_chars = config.CHUNK_OVERLAP_TOKENS * config.CHARS_PER_TOKEN
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            # Prefer to break at the end of a sentence in the last 20% of the window.
            cut = max(text.rfind(p, start + int(max_chars * 0.8), end) for p in (". ", "? ", "! ", "\n"))
            if cut != -1:
                end = cut + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap_chars, start + 1)
    return chunks
