import argparse
import csv
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import requests

import config
from summarizer.summarize import summarize
from summarizer.transcript import parse
from summarizer.upload_validation import decode

JUDGE_PROMPT = (
    "You check summaries of university lectures. Below is a lecture transcript and the numbered "
    "bullet points of its summary.\n"
    "Score EVERY bullet point:\n"
    " 1 = important and correct\n"
    " 0 = correct but not important\n"
    "-1 = wrong, or not in the transcript\n"
    "Answer with one line per bullet point in the form 'number: score', for example:\n"
    "1: 1\n2: -1\n3: 0\n"
    "Write nothing else.\n\n"
    "TRANSCRIPT:\n{transcript}\n\nBULLET POINTS:\n{bullets}"
)

JUDGE_TIMEOUT_S = 900  # the judge reads a whole transcript per request; slow laptops need time
SUMMARIES_FILE = Path("evaluation/summaries.json")
FIELDS = ["lecture", "detail_level", "bullet_no", "bullet", "score"]
SCORE_LINE = re.compile(r"^\s*(\d+)\s*[:.)=]\s*(-?\d+)")


def summary_bullets(body: str) -> list[str]:
    """The bullets under '## Summary' only, not the topics or the action items."""
    section = body.split("## Summary", 1)[-1].split("## Action items", 1)[0]
    return [line[2:].strip() for line in section.splitlines() if line.startswith("- ")]


def clamp(score: int) -> int:
    return max(-1, min(1, score))


def parse_scores(answer: str, count: int) -> list[Optional[int]]:
    """Turn the judge's answer ('1: 1', '2: -1', ...) into exactly `count` scores.
    A bullet the judge skipped gets None (left out of the averages), not a made-up 0."""
    found = {}
    for line in answer.splitlines():
        match = SCORE_LINE.match(line)
        if match:
            found[int(match.group(1))] = clamp(int(match.group(2)))
    if found:
        return [found.get(number) for number in range(1, count + 1)]
    # No 'number: score' lines: take the numbers in order (e.g. the answer "1 -1 0").
    numbers = [clamp(int(n)) for n in re.findall(r"-?\d+", answer)]
    return (numbers + [None] * count)[:count]


def ask_judge(model: str, transcript: str, bullets: list[str]) -> list[Optional[int]]:
    """One request per summary: the judge reads the transcript once and scores all its bullets."""
    numbered = "\n".join(f"{i}. {bullet}" for i, bullet in enumerate(bullets, start=1))
    response = requests.post(
        f"{config.LMSTUDIO_BASE_URL}/chat/completions",
        json={
            "model": model,
            "messages": [{"role": "user", "content": JUDGE_PROMPT.format(transcript=transcript, bullets=numbered)}],
            "temperature": 0,  # the judge should always give the same score for the same bullet
            "max_tokens": 10 * len(bullets) + 20,  # only short 'number: score' lines are needed
        },
        timeout=JUDGE_TIMEOUT_S,
    )
    response.raise_for_status()
    return parse_scores(response.json()["choices"][0]["message"]["content"], len(bullets))


def swap_models(judge_model: str) -> None:
    """Unload the summary model and load the judge, using LM Studio's command line tool 'lms'.
    Without 'lms' (or if it fails) we ask the user to swap the models by hand."""
    lms = shutil.which("lms")
    if lms:
        print("\nSwapping models in LM Studio ...")
        unloaded = subprocess.run([lms, "unload", "--all"]).returncode == 0
        loaded = unloaded and subprocess.run(
            [lms, "load", judge_model, "--context-length", "16384", "--identifier", judge_model, "--yes"]
        ).returncode == 0
        if loaded:
            return
        print("Automatic swap did not work.")
    input("\nIn LM Studio, eject the summary model, load the judge model, then press Enter ...")


def make_summaries() -> list[dict]:
    work = []
    for path in sorted(Path("transcripts").glob("*.txt")):
        transcript = parse(decode(path.read_bytes()))
        for level in config.DETAIL_LEVELS:
            print(f"Summarizing {path.name} ({level}) ...")
            bullets = summary_bullets(summarize(transcript, level).body)
            work.append({"lecture": path.stem, "level": level, "text": transcript.text, "bullets": bullets})
    return work


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--judge-model", required=True, help="the judge model's id as shown in LM Studio")
    parser.add_argument("--out", default="evaluation/judge_scores.csv")
    parser.add_argument("--fresh", action="store_true", help="write new summaries even if saved ones exist")
    args = parser.parse_args()

    # Step 1: all summaries with the normal model, or the saved ones from an earlier run.
    if SUMMARIES_FILE.exists() and not args.fresh:
        work = json.loads(SUMMARIES_FILE.read_text(encoding="utf-8"))
        print(f"Using the saved summaries in {SUMMARIES_FILE} (add --fresh to make new ones).")
    else:
        work = make_summaries()
        SUMMARIES_FILE.write_text(json.dumps(work, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nAll summaries are done and saved in {SUMMARIES_FILE}.")

    # Laptops that can only hold one model: swap models here.
    swap_models(args.judge_model)

    # Step 2: the judge scores all bullets of each summary in one request.
    rows = []
    for item in work:
        print(f"Judging {item['lecture']} ({item['level']}) ...")
        scores = ask_judge(args.judge_model, item["text"], item["bullets"])
        for number, (bullet, score) in enumerate(zip(item["bullets"], scores), start=1):
            rows.append({"lecture": item["lecture"], "detail_level": item["level"], "bullet_no": number,
                         "bullet": bullet, "score": score})

    with open(args.out, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} scores to {args.out}")
    for level in config.DETAIL_LEVELS:
        level_rows = [row for row in rows if row["detail_level"] == level]
        scores = [row["score"] for row in level_rows if row["score"] is not None]
        if scores:
            wrong = scores.count(-1)
            print(f"{level:9} average {sum(scores) / len(scores):+.2f}   wrong or invented: {wrong} of {len(scores)}")


if __name__ == "__main__":
    main()