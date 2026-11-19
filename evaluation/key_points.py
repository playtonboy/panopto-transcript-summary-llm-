"""Key point check: are the most important points of each lecture kept in its summaries?

Write the key points of each lecture by hand in evaluation/key_points.json (it stays on your laptop):
    {"secsai_l03_80min_en": ["Assignment 2 is due Friday 20 Nov at 12:00", "...", "..."]}
The file name without .txt is the key. Then make the summaries with evaluation.judge and run:
    python -m evaluation.key_points --model <id of the loaded model>
"""

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

import config
from evaluation.judge import SUMMARIES_FILE
from evaluation.matching import key_points_found

KEY_POINTS_FILE = Path("evaluation/key_points.json")
FIELDS = ["lecture", "detail_level", "key_point", "found"]


def recall(found: List[Optional[bool]]) -> float:
    """Share of key points found; an unanswered point counts as missing."""
    return sum(answer is True for answer in found) / len(found) if found else 0.0


def summary_text(item: Dict) -> str:
    """The whole summary if it was saved, otherwise only its bullets."""
    return item.get("body") or "\n".join(f"- {bullet}" for bullet in item["bullets"])


def main() -> None:
    """Check every saved summary against the key points of its lecture and print the share found."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=config.MODEL_NAME, help="model that checks the summaries")
    parser.add_argument("--out", default="evaluation/key_points.csv")
    args = parser.parse_args()

    key_points = json.loads(KEY_POINTS_FILE.read_text(encoding="utf-8"))
    work = json.loads(SUMMARIES_FILE.read_text(encoding="utf-8"))
    rows, totals = [], {level: [] for level in config.DETAIL_LEVELS}
    for item in work:
        points = key_points.get(item["lecture"])
        if not points:
            continue
        if "body" not in item:
            print(
                f"{item['lecture']}: only the bullets were saved; run evaluation.judge --fresh to include action items"
            )
        found = key_points_found(summary_text(item), points, args.model)
        totals.setdefault(item["level"], []).extend(found)
        print(f"{item['lecture']:30} {item['level']:9} {recall(found):.0%} of {len(points)} key points")
        rows += [
            {"lecture": item["lecture"], "detail_level": item["level"], "key_point": point, "found": answer}
            for point, answer in zip(points, found)
        ]

    with open(args.out, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print()
    for level, found in totals.items():
        if found:
            print(f"All lectures, {level:9} {recall(found):.0%} of {len(found)} key points kept")


if __name__ == "__main__":
    main()
