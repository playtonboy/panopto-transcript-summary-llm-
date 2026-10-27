"""Speed check (SCRUM-44): times one summary per transcript in transcripts/.

    python -m evaluation.timing
"""

import time
from pathlib import Path

import config
from summarizer.chunking import split_into_chunks
from summarizer.summarize import summarize
from summarizer.transcript import parse

print(f"CHUNK_TOKENS={config.CHUNK_TOKENS}  CHUNK_OVERLAP_TOKENS={config.CHUNK_OVERLAP_TOKENS}")
for path in sorted(Path("transcripts").glob("*.txt")):
    transcript = parse(path.read_text(encoding="utf-8", errors="replace"))
    start = time.perf_counter()
    summarize(transcript, "Medium")
    seconds = time.perf_counter() - start
    parts = len(split_into_chunks(transcript.text))
    flag = "OK" if seconds < 120 else "TOO SLOW"
    print(f"{path.name}: {transcript.word_count} words, {parts} part(s), {seconds:.0f} s  {flag}")
