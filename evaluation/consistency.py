"""Consistency check (SCRUM-33): summarizes the same lecture 5 times and compares the bullets.

Start LM Studio first, then run from the project folder:
    python -m evaluation.consistency transcripts/secsai_l03_80min_en.txt
"""

import sys
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

import config
from evaluation.judge import summary_bullets
from summarizer.summarize import summarize
from summarizer.transcript import parse
from summarizer.upload_validation import decode

RUNS = 5
SAME = 0.6  # two bullets count as "the same point" when their text is at least 60% alike


def overlap(a: list[str], b: list[str]) -> float:
    """Share of the bullets in a that have a matching bullet in b (0.0 to 1.0)."""
    if not a:
        return 0.0
    matches = sum(any(SequenceMatcher(None, x.lower(), y.lower()).ratio() >= SAME for y in b) for x in a)
    return matches / len(a)


def main() -> None:
    path = Path(sys.argv[1])
    transcript = parse(decode(path.read_bytes()))
    print(f"{path.name}, TEMPERATURE={config.TEMPERATURE}, detail level Medium")

    runs = []
    for i in range(1, RUNS + 1):
        print(f"Run {i} of {RUNS} ...")
        runs.append(summary_bullets(summarize(transcript, "Medium").body))

    scores = [overlap(a, b) for a, b in combinations(runs, 2)]
    print(f"\nAverage bullet overlap over {len(scores)} pairs: {sum(scores) / len(scores):.0%}")
    print("Bullets per run:", [len(run) for run in runs])
    print("\nRun 1 for reference:")
    for bullet in runs[0]:
        print(" -", bullet)


if __name__ == "__main__":
    main()
