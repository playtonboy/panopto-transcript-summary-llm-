"""Minimal client for the LM Studio local server (OpenAI-compatible API).

Everything stays on localhost, so transcripts never leave the user's computer (NFR4, NFR10).
"""

import requests

import config


class LLMError(RuntimeError):
    """Raised when the local model cannot produce an answer. The message is shown to the user."""


def chat(system_prompt: str, user_prompt: str) -> str:
    payload = {
        "model": config.MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": config.TEMPERATURE,
        "max_tokens": config.MAX_OUTPUT_TOKENS,
        "stream": False,
    }
    try:
        response = requests.post(
            f"{config.LMSTUDIO_BASE_URL}/chat/completions",
            json=payload,
            timeout=config.REQUEST_TIMEOUT_S,
        )
    except requests.ConnectionError as exc:
        raise LLMError(
            "Could not reach LM Studio. Open LM Studio, load a model and start the local server."
        ) from exc
    except requests.Timeout as exc:
        raise LLMError("The model took too long to answer. Please try again.") from exc

    if response.status_code != 200:
        raise LLMError(f"Could not generate summary, please try again (LM Studio returned {response.status_code}).")
    try:
        return response.json()["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, ValueError) as exc:
        raise LLMError("Could not generate summary, please try again.") from exc


def is_server_running() -> bool:
    try:
        return requests.get(f"{config.LMSTUDIO_BASE_URL}/models", timeout=3).ok
    except requests.RequestException:
        return False
