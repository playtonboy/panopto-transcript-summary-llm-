"""Consistency check: summarizes the same lecture several times and compares the points by meaning.

Start LM Studio first, then run from the project folder:
    python -m evaluation.consistency transcripts/<lecture>.txt
"""

import argparse
from itertools import combinations
from pathlib import Path
from typing import Callable, List, Optional

import config
from evaluation.judge import summary_bullets
from evaluation.matching import same_points
from summarizer.summarize import summarize
from summarizer.transcript import parse
from summarizer.upload_validation import decode

RUNS = 5

# Pairs from our lecturer's feedback: a letter-based match got all three wrong.
CHECK_PAIRS = [
    ("The assignment is due Friday at noon.", "The assignment must be handed in by 12:00 on Friday.", True),
    ("The exam is on Monday.", "The exam is on Tuesday.", False),
    ("The assignment is due Friday at noon.", "The assignment is due Friday at 17:00.", False),
]

Matcher = Callable[[List[str], List[str]], List[Optional[bool]]]


def overlap(a: List[str], b: List[str], same: Matcher) -> float:
    """Share of the points in a that have a point with the same meaning in b (0.0 to 1.0)."""
    if not a:
        return 0.0
    return sum(answer is True for answer in same(a, b)) / len(a)


def check_matcher(same: Matcher) -> int:
    """Run the known pairs through the matcher and print the result; returns how many it got right."""
    right = 0
    for first, second, expected in CHECK_PAIRS:
        answer = same([first], [second])[0]
        right += answer == expected
        print(f"  {'ok  ' if answer == expected else 'WRONG'} same={answer}: '{first}' / '{second}'")
    return right


def main() -> None:
    """Summarize one lecture RUNS times and print the average overlap between the runs."""
    parser = argparse.ArgumentParser()
    parser.add_argument("transcript", type=Path)
    parser.add_argument("--runs", type=int, default=RUNS)
    parser.add_argument("--model", default=config.MODEL_NAME, help="model that decides if two points are the same")
    args = parser.parse_args()

    def same(a: List[str], b: List[str]) -> List[Optional[bool]]:
        return same_points(a, b, args.model)

    print("Checking the matcher on known pairs:")
    print(f"{check_matcher(same)} of {len(CHECK_PAIRS)} right\n")

    transcript = parse(decode(args.transcript.read_bytes()))
    print(f"{args.transcript.name}, TEMPERATURE={config.TEMPERATURE}, detail level Medium")
    runs = []
    for i in range(1, args.runs + 1):
        print(f"Run {i} of {args.runs} ...")
        runs.append(summary_bullets(summarize(transcript, "Medium").body))

    scores = [overlap(a, b, same) for a, b in combinations(runs, 2)]
    print(f"\nAverage overlap by meaning over {len(scores)} pairs: {sum(scores) / len(scores):.0%}")
    print("Points per run:", [len(run) for run in runs])
    print("\nRun 1 for reference:")
    for bullet in runs[0]:
        print(" -", bullet)


if __name__ == "__main__":
    main()
