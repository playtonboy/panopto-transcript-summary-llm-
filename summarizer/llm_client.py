"""Talks to the LM Studio local server. Everything stays on localhost (NFR4, NFR10)."""

import requests
from typing import List, Optional
import config


class LLMError(RuntimeError):
    """Error whose message is shown to the user (UR11)."""


def chat(system_prompt: str, user_prompt: str) -> str:
    payload = {
        "model": config.MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": config.TEMPERATURE,
        "max_tokens": config.MAX_OUTPUT_TOKENS,
    }
    try:
        response = requests.post(
            f"{config.LMSTUDIO_BASE_URL}/chat/completions",
            json=payload,
            timeout=config.REQUEST_TIMEOUT_S,
        )
    except requests.ConnectionError as exc:
        raise LLMError("Could not reach LM Studio. Open LM Studio, load a model and start the local server.") from exc
    except requests.Timeout as exc:
        raise LLMError("The model took too long to answer. Please try again.") from exc

    if response.status_code != 200:
        raise LLMError(f"Could not generate a summary (LM Studio returned {response.status_code}).")
    try:
        return response.json()["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, ValueError) as exc:
        raise LLMError("Could not generate a summary, please try again.") from exc


def is_server_running() -> bool:
    try:
        return requests.get(f"{config.LMSTUDIO_BASE_URL}/models", timeout=3).ok
    except requests.RequestException:
        return False

def loaded_models() -> List[str]:
    try:
        response = requests.get(f"{config.LMSTUDIO_BASE_URL}/models", timeout=3)
        return [model["id"] for model in response.json()["data"]] if response.ok else []
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return []


def model_warning() -> Optional[str]:
    models = loaded_models()
    if not models:
        return "LM Studio is not reachable. Open LM Studio, load a model and start the local server."
    if config.MODEL_NAME not in models:
        return (
            f"config.MODEL_NAME is '{config.MODEL_NAME}', but LM Studio has loaded: {', '.join(models)}. "
            "Load that model, or start the worker with --model <id> using one of these ids."
        )
    return None