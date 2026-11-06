#!/usr/bin/env bash
# One-click start for macOS, Linux and Git Bash on Windows (SCRUM-14).
# Creates the venv, installs the requirements, starts the orchestrator, an AI worker and the Streamlit
# interface, then opens the app. Run it with:  bash start.sh      Stop everything with Ctrl+C.
# Services whose code is not there yet (orchestrator/, worker/) are skipped.
set -e
cd "$(dirname "$0")"

# 1. Python virtual environment
if [ ! -d .venv ]; then
    echo "Creating the virtual environment (.venv)..."
    if command -v python3 >/dev/null 2>&1 && python3 -c "import sys" >/dev/null 2>&1; then
        python3 -m venv .venv
    else
        python -m venv .venv
    fi
fi
if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=.venv/Scripts/python.exe; fi

# 2. Requirements (only when requirements.txt changed since the last start)
if "$PY" scripts/start_helper.py deps-changed; then
    echo "Installing requirements..."
    "$PY" -m pip install --quiet --upgrade pip
    "$PY" -m pip install --quiet -r requirements.txt
    "$PY" scripts/start_helper.py deps-saved
fi

"$PY" scripts/start_helper.py check-lmstudio

# Stop the background services when this script stops (Ctrl+C or closing the app).
PIDS=()
cleanup() { [ ${#PIDS[@]} -gt 0 ] && kill "${PIDS[@]}" 2>/dev/null; true; }
trap cleanup EXIT INT TERM

# 3. Orchestrator (job queue) on localhost:8000
if [ -f orchestrator/main.py ]; then
    if "$PY" scripts/start_helper.py is-up http://localhost:8000/health; then
        echo "Orchestrator is already running."
    else
        echo "Starting the orchestrator..."
        "$PY" -m uvicorn orchestrator.main:app --host 127.0.0.1 --port 8000 --log-level warning &
        PIDS+=($!)
        "$PY" scripts/start_helper.py wait http://localhost:8000/health 30 \
            || { echo "ERROR: the orchestrator did not start."; exit 1; }
    fi
fi

# 4. AI worker (talks to LM Studio)
if [ -f worker/main.py ]; then
    echo "Starting an AI worker..."
    "$PY" -m worker.main &
    PIDS+=($!)
fi

# 5. Interface: open the browser as soon as it is up, then run Streamlit until Ctrl+C
echo "Starting the app on http://localhost:8501 ..."
"$PY" scripts/start_helper.py open http://localhost:8501 60 &
PIDS+=($!)
"$PY" -m streamlit run app.py --server.headless true --server.port 8501
