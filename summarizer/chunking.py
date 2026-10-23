import config

SENTENCE_ENDS = (". ", "? ", "! ", "\n")


def estimate_tokens(text: str) -> int:
    return len(text) // config.CHARS_PER_TOKEN + 1


def split_into_chunks(text: str) -> list[str]:
    max_chars = config.CHUNK_TOKENS * config.CHARS_PER_TOKEN
    overlap_chars = config.CHUNK_OVERLAP_TOKENS * config.CHARS_PER_TOKEN

    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))

        # Not at the end yet: move back to a sentence end in the last 20%
        if end < len(text):
            min_end = start + int(max_chars * 0.8)
            best = -1
            for sep in SENTENCE_ENDS:
                pos = text.rfind(sep, min_end, end)
                if pos != -1:
                    best = max(best, pos + len(sep))
            if best != -1:
                end = best

        chunks.append(text[start:end])
        if end >= len(text):
            break
        # Overlap, but always move forward
        start = max(end - overlap_chars, start + 1)

    return chunks