"""Yes/no questions to the local model about numbered points, used by the evaluation scripts."""

import re
from typing import List, Optional

import requests

import config

ANSWER_LINE = re.compile(r"^\s*(\d+)\s*[:.)=-]\s*(yes|no)\b", re.IGNORECASE)

SAME_POINT_PROMPT = (
    "Below are two lists of points from two summaries of the same lecture.\n"
    "For EVERY point in list A, answer 'yes' if some point in list B says the same thing, and 'no' if not.\n"
    "Different wording is fine, but a different date, time, number or name makes it a different point.\n"
    "Answer with one line per point of list A in the form 'number: yes' or 'number: no'. Write nothing else.\n\n"
    "LIST A:\n{a}\n\nLIST B:\n{b}"
)

KEY_POINT_PROMPT = (
    "Below is a summary of a lecture and a numbered list of key points from that lecture.\n"
    "For EVERY key point, answer 'yes' if the summary contains it, and 'no' if it is missing.\n"
    "Different wording is fine, but a changed fact (another date, number or name) counts as 'no'.\n"
    "Answer with one line per key point in the form 'number: yes' or 'number: no'. Write nothing else.\n\n"
    "SUMMARY:\n{summary}\n\nKEY POINTS:\n{points}"
)


def numbered(items: List[str]) -> str:
    """The items as a numbered list, one per line."""
    return "\n".join(f"{number}. {item}" for number, item in enumerate(items, start=1))


def parse_yes_no(answer: str, count: int) -> List[Optional[bool]]:
    """Turn 'number: yes/no' lines into exactly `count` answers; a skipped number gives None."""
    found = {}
    for line in answer.splitlines():
        match = ANSWER_LINE.match(line)
        if match:
            found[int(match.group(1))] = match.group(2).lower() == "yes"
    return [found.get(number) for number in range(1, count + 1)]


def ask(prompt: str, count: int, model: str) -> List[Optional[bool]]:
    """Ask the model one yes/no question per numbered point, at temperature 0 so the answer is repeatable."""
    response = requests.post(
        f"{config.LMSTUDIO_BASE_URL}/chat/completions",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 8 * count + 20,
        },
        timeout=config.REQUEST_TIMEOUT_S,
    )
    response.raise_for_status()
    return parse_yes_no(response.json()["choices"][0]["message"]["content"], count)


def same_points(a: List[str], b: List[str], model: str) -> List[Optional[bool]]:
    """For each point in a: does b contain a point with the same meaning?"""
    if not a or not b:
        return [False] * len(a)
    return ask(SAME_POINT_PROMPT.format(a=numbered(a), b=numbered(b)), len(a), model)


def key_points_found(summary: str, points: List[str], model: str) -> List[Optional[bool]]:
    """For each key point: is it in the summary?"""
    return ask(KEY_POINT_PROMPT.format(summary=summary, points=numbered(points)), len(points), model)
