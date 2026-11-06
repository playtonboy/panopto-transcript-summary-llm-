@echo off
rem One-click start for Windows (SCRUM-14): double-click this file.
rem Creates the venv, installs the requirements, starts the orchestrator, an AI worker and the Streamlit
rem interface, then opens the app. Services whose code is not there yet (orchestrator\, worker\) are skipped.
setlocal
cd /d "%~dp0"

rem 1. Python virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo Creating the virtual environment ^(.venv^)...
    py -3 -m venv .venv 2>nul || python -m venv .venv
    if not exist ".venv\Scripts\python.exe" (
        echo ERROR: Python was not found. Install Python 3 from python.org and tick "Add python.exe to PATH".
        pause
        exit /b 1
    )
)
set "PY=%CD%\.venv\Scripts\python.exe"

rem 2. Requirements (only when requirements.txt changed since the last start)
"%PY%" scripts\start_helper.py deps-changed
if not errorlevel 1 (
    echo Installing requirements...
    "%PY%" -m pip install --quiet --upgrade pip
    "%PY%" -m pip install --quiet -r requirements.txt || (echo ERROR: installing the requirements failed. & pause & exit /b 1)
    "%PY%" scripts\start_helper.py deps-saved
)

"%PY%" scripts\start_helper.py check-lmstudio

rem 3. Orchestrator (job queue) on localhost:8000, in its own minimized window
if exist "orchestrator\main.py" (
    "%PY%" scripts\start_helper.py is-up http://localhost:8000/health
    if errorlevel 1 (
        echo Starting the orchestrator...
        start "Lecture Summarizer - orchestrator" /min "%PY%" -m uvicorn orchestrator.main:app --host 127.0.0.1 --port 8000 --log-level warning
        "%PY%" scripts\start_helper.py wait http://localhost:8000/health 30
        if errorlevel 1 (echo ERROR: the orchestrator did not start. & pause & exit /b 1)
    ) else (
        echo Orchestrator is already running.
    )
)

rem 4. AI worker (talks to LM Studio), in its own minimized window
if exist "worker\main.py" (
    echo Starting an AI worker...
    start "Lecture Summarizer - worker" /min "%PY%" -m worker.main
)

rem 5. Interface: open the browser as soon as it is up, then run Streamlit in this window
echo Starting the app on http://localhost:8501 ...
echo To stop: press Ctrl+C in this window and answer N to "Terminate batch job", so the other windows close too.
start "" /b "%PY%" scripts\start_helper.py open http://localhost:8501 60
"%PY%" -m streamlit run app.py --server.headless true --server.port 8501

rem Streamlit stopped: also stop the background services
taskkill /f /fi "WINDOWTITLE eq Lecture Summarizer - orchestrator*" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq Lecture Summarizer - worker*" >nul 2>&1
endlocal
