"""Small helper for start.sh / start.bat (SCRUM-14). Works on Python 3.8+ and uses only the standard library.

    python scripts/start_helper.py deps-changed          exit 0 if requirements.txt changed since the last install
    python scripts/start_helper.py deps-saved            remember the current requirements.txt as installed
    python scripts/start_helper.py check-lmstudio        print a warning if LM Studio's server is not reachable
    python scripts/start_helper.py is-up URL             exit 0 if URL answers, else 1
    python scripts/start_helper.py wait URL SECONDS      wait until URL answers; exit 1 after SECONDS
    python scripts/start_helper.py open URL SECONDS      wait until URL answers, then open it in the browser
"""

import hashlib
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAMP = ROOT / ".venv" / "requirements.sha256"  # inside the git-ignored .venv folder

sys.path.insert(0, str(ROOT))
import config  # noqa: E402


def requirements_hash() -> str:
    return hashlib.sha256((ROOT / "requirements.txt").read_bytes()).hexdigest()


def is_up(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.status < 500
    except Exception:
        return False


def wait_until_up(url: str, seconds: float) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if is_up(url):
            return True
        time.sleep(0.5)
    return False


def main(args) -> int:
    command = args[0] if args else ""
    if command == "deps-changed":
        return 0 if not STAMP.exists() or STAMP.read_text().strip() != requirements_hash() else 1
    if command == "deps-saved":
        STAMP.write_text(requirements_hash())
        return 0
    if command == "check-lmstudio":
        if not is_up(config.LMSTUDIO_BASE_URL + "/models"):
            print("WARNING: LM Studio is not running. Open LM Studio, load the model and start the local server.")
        return 0
    if command == "is-up":
        return 0 if is_up(args[1]) else 1
    if command == "wait":
        return 0 if wait_until_up(args[1], float(args[2])) else 1
    if command == "open":
        if wait_until_up(args[1], float(args[2])):
            webbrowser.open(args[1])
            return 0
        return 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
