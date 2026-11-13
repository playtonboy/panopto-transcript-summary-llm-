# panopto-transcript-summary-llm-

**New here?** Follow the [installation guide](docs/INSTALL.md).

description.

## Privacy (SCRUM-29: NFR3, NFR4, NFR10)

The app runs only on your own computer. Transcripts and summaries are never written to disk and never sent to the internet.

| What | How it works | Checked by |
| --- | --- | --- |
| Model calls | Only `http://localhost:1234/v1` (LM Studio on this computer), see `config.LMSTUDIO_BASE_URL` | `tests/test_privacy.py` records every connection during a full run (English and Dutch transcript, every summary language): only `127.0.0.1` |
| Disk | Upload, transcript and summary stay in memory; `.txt` / `.docx` are built in memory (`io.BytesIO`) and only saved when you click a download button | `tests/test_privacy.py` fails if any file is opened for writing during a full run |
| After a summary | Only the summary is kept in `st.session_state` (so it survives button clicks); the transcript text is not kept. Closing or refreshing the tab removes everything | `tests/test_privacy.py` |
| Streamlit | `.streamlit/config.toml`: `gatherUsageStats = false` (no usage statistics sent to Streamlit) and `address = "localhost"` (others on the same Wi-Fi cannot open the app) | `tests/test_privacy.py` + manual check below |

Manual check: ran the app, generated a summary and downloaded it while recording network traffic.

- Before the fix, Streamlit tried to reach `data.streamlit.io` (usage statistics) and `checkip.amazonaws.com` (to show a "Network URL").
- After the fix, the app server and the browser only contacted `localhost` (the app itself and LM Studio on `localhost:1234`).

Developer tools in `evaluation/` (not part of the app): they also only call LM Studio on `localhost`. They read test transcripts from the git-ignored `transcripts/` folder, and evaluation scripts may save their results next to them. Use only transcripts you are allowed to keep on your computer, and never commit them.

Outside this app: LM Studio is a separate program on the same computer and runs the model locally. Its Developer Logs show the requests it receives and it may keep its own log files on this computer. LM Studio itself goes online only for its own updates and model downloads.

Run the checks yourself: `python -m pytest tests/test_privacy.py -v`. There is no job queue or other storage in the code yet; if one is added later, these tests must still pass.
