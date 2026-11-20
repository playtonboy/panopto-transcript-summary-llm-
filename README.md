# panopto-transcript-summary-llm-

**Panopto Lecture Summarizer**: turns a Panopto lecture transcript into a structured summary: the main topics, the key points and the action items (deadlines, assignments, readings). Everything runs on your own computer with a local AI model in LM Studio, so transcripts never leave your laptop.

Course project of Group 4 (Ege, Burak, Siem, Frida, Platon), Software Engineering 2026.

## Features

| Feature | Where |
| --- | --- |
| Upload a Panopto .txt transcript, or paste the text | `app.py`, `summarizer/upload_validation.py` |
| Timestamps, line numbers and filler removed; speakers recognised | `summarizer/transcript.py` |
| Three detail levels: Short (5 points), Medium (10), Detailed (15) | `config.DETAIL_LEVELS` |
| Summary in English, Dutch or German, from English, Dutch or mixed lectures | `summarizer/summarize.py` |
| Long lectures split into parts and summarized part by part | `summarizer/chunking.py`, `summarize.py` |
| Download as .txt, .docx or .pdf, or copy with one click; AI disclaimer on every output | `summarizer/export.py` |
| Regenerate with other settings; the last 5 summaries of this session stay visible | `app.py` |
| Interface, orchestrator and AI workers as separate services | `app.py`, `orchestrator/`, `worker/`, see [docs/architecture.md](docs/architecture.md) |
| Evaluation: LLM-as-judge, consistency, key points and timing | `evaluation/` |

## Install

Full step-by-step guide with screenshots: [docs/INSTALL.md](docs/INSTALL.md). In short:

1. Install Python (3.11 or newer is recommended; 3.9 and 3.10 also work) and LM Studio.
2. In LM Studio, download Qwen2.5 7B Instruct, load it with a context length of 16384, and start the local server (Developer tab, port 1234).
3. Get the code: `git clone https://github.com/playtonboy/panopto-transcript-summary-llm-.git`

## Run

Start LM Studio's server first, then double-click `start.bat` (Windows) or run `./start.sh` (macOS/Linux). The script creates a virtual environment, installs the requirements and starts the three services. The app opens at http://localhost:8501.

Or start the services yourself, each in its own terminal:

```
python -m uvicorn orchestrator.main:app --port 8000
python -m worker.main
streamlit run app.py
```

Start a second `python -m worker.main` to summarize two lectures at the same time.

## Configuration

All settings are in `config.py`.

| Setting | Default | Meaning |
| --- | --- | --- |
| `MODEL_NAME` | `qwen2.5-7b-instruct` | API id of the model in LM Studio (`lms ls` shows it). Override per worker: `python -m worker.main --model <id>` |
| `LMSTUDIO_BASE_URL` | `http://localhost:1234/v1` | LM Studio's local server |
| `ORCHESTRATOR_URL` | `http://localhost:8000` | The orchestrator. Can also be changed in the app's sidebar (localhost only) |
| `TEMPERATURE` | `0.2` | Lower = more consistent summaries |
| `DETAIL_LEVELS` | Short 5, Medium 10, Detailed 15 | Number of key points per level |
| `OUTPUT_LANGUAGES` | English, Dutch, German | Languages the summary can be written in |
| `MAX_UPLOAD_MB` | `5` | Largest transcript you can upload |
| `REQUEST_TIMEOUT_S` | `300` | How long one model request may take |
| `CHUNK_TOKENS` | `12000` | Size of one part of a long transcript |
| `JOB_STALE_S`, `JOB_MAX_ATTEMPTS` | 360 s, 2 | When a stopped worker's job is retried, and how often |
| `HEARTBEAT_S` | 30 s | How often a busy worker tells the orchestrator it is still working |
| `JOB_KEEP_S` | 600 s | Finished jobs are removed from memory after this long |

## Tests

```
python -m pytest -v
```

No LM Studio is needed: the tests use a fake LM Studio server. GitHub Actions runs them on every push and pull request.

## Troubleshooting

| You see | Fix |
| --- | --- |
| "The summarizer service is not running" | Start the orchestrator (`start.bat` / `start.sh`, or the uvicorn command above) |
| "Waiting for an AI worker" | Start a worker: `python -m worker.main` |
| "Could not reach LM Studio" | Open LM Studio, load the model and press Start Server in the Developer tab |
| "LM Studio returned 400" | The context length is too small: reload the model with context length 16384 |
| "LM Studio returned 404" or the worker warns about the model | `MODEL_NAME` does not match the loaded model. Run `lms ls`, then use that id with `--model` |
| `pytest: command not found` | Use `python -m pytest` with the virtual environment active |
| Summary takes very long | Normal for a 2 h lecture on a laptop without a GPU. Use Short, or close other programs |

## Privacy (SCRUM-29: NFR3, NFR4, NFR10)

The app runs only on your own computer. Transcripts and summaries are never written to disk and never sent to the internet.

| What | How it works | Checked by |
| --- | --- | --- |
| Model calls | Only `http://localhost:1234/v1` (LM Studio on this computer), see `config.LMSTUDIO_BASE_URL` | `tests/test_privacy.py` records every connection during a full run (English and Dutch transcript, every summary language): only `127.0.0.1` |
| Disk | Upload, transcript and summary stay in memory; `.txt` / `.docx` / `.pdf` are built in memory (`io.BytesIO`) and only saved when you click a download button | `tests/test_privacy.py` fails if any file is opened for writing during a full run |
| Job queue | The orchestrator keeps its queue in memory only (in-memory SQLite). The transcript is deleted from a job as soon as it is done or failed, and finished jobs are removed after `JOB_KEEP_S` | `tests/test_orchestrator.py` |
| After a summary | The summary and the last transcript stay in `st.session_state` (in memory), so you can download, copy or press Regenerate without uploading again. Closing or refreshing the tab removes everything | `tests/test_privacy.py` |
| Streamlit | `.streamlit/config.toml`: `gatherUsageStats = false` (no usage statistics sent to Streamlit), `address = "localhost"` (others on the same Wi-Fi cannot open the app) and `toolbarMode = "viewer"` (no "Deploy" button) | `tests/test_privacy.py` + manual check below |

Manual check: ran the app, generated a summary and downloaded it while recording network traffic.

- Before the fix, Streamlit tried to reach `data.streamlit.io` (usage statistics) and `checkip.amazonaws.com` (to show a "Network URL").
- After the fix, the app server and the browser only contacted `localhost` (the app itself and LM Studio on `localhost:1234`).

Developer tools in `evaluation/` (not part of the app): they also only call LM Studio on `localhost`. They read test transcripts from the git-ignored `transcripts/` folder, and evaluation scripts may save their results next to them. Use only transcripts you are allowed to keep on your computer, and never commit them.

Outside this app: LM Studio is a separate program on the same computer and runs the model locally. Its Developer Logs show the requests it receives and it may keep its own log files on this computer. LM Studio itself goes online only for its own updates and model downloads.

Run the checks yourself: `python -m pytest tests/test_privacy.py tests/test_orchestrator.py -v`.
