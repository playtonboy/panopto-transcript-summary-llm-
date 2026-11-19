"""Judge scores as a Markdown table for the final report."""

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import config

Key = Tuple[str, str]


def read_scores(path: Path) -> Dict[Key, List[int]]:
    """Scores per lecture and detail level, skipping unscored bullets."""
    scores: Dict[Key, List[int]] = defaultdict(list)
    with open(path, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if row["score"].strip():
                scores[(row["lecture"], row["detail_level"])].append(int(row["score"]))
    return scores


def stats(scores: List[int]) -> Tuple[float, int, int]:
    """Average, number of -1 scores and number of scores."""
    return sum(scores) / len(scores), scores.count(-1), len(scores)


def _level_order(key: Key) -> Tuple[str, int]:
    levels = list(config.DETAIL_LEVELS)
    return key[0], levels.index(key[1]) if key[1] in levels else len(levels)


def table(after: Dict[Key, List[int]], before: Optional[Dict[Key, List[int]]] = None) -> str:
    """Markdown table with one row per lecture and level, plus totals."""
    header = "| Lecture | Detail level | Average (-1 to 1) | Wrong or invented |"
    lines = [header, "| --- | --- | --- | --- |"]
    if before is not None:
        lines = [header + " Average before |", "| --- | --- | --- | --- | --- |"]

    totals: Dict[str, List[int]] = defaultdict(list)
    totals_before: Dict[str, List[int]] = defaultdict(list)
    for key in sorted(after, key=_level_order):
        average, wrong, count = stats(after[key])
        totals[key[1]].extend(after[key])
        line = f"| {key[0]} | {key[1]} | {average:+.2f} | {wrong} of {count} |"
        if before is not None:
            earlier = before.get(key)
            totals_before[key[1]].extend(earlier or [])
            line += f" {stats(earlier)[0]:+.2f} |" if earlier else " - |"
        lines.append(line)

    for level in [lvl for lvl in config.DETAIL_LEVELS if lvl in totals]:
        average, wrong, count = stats(totals[level])
        line = f"| **All lectures** | {level} | **{average:+.2f}** | {wrong} of {count} |"
        if before is not None:
            line += f" {stats(totals_before[level])[0]:+.2f} |" if totals_before[level] else " - |"
        lines.append(line)
    return "\n".join(lines)


def main() -> None:
    """Read the judge CSV file(s) and print the table."""
    parser = argparse.ArgumentParser()
    parser.add_argument("scores", type=Path, help="CSV from evaluation.judge")
    parser.add_argument("--before", type=Path, help="older CSV to compare with")
    args = parser.parse_args()
    print(table(read_scores(args.scores), read_scores(args.before) if args.before else None))


if __name__ == "__main__":
    main()
