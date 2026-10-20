# Panopto Transcript Summary (local LLM)

Summarize Panopto lecture transcripts **privately**, using a language model that runs on your own laptop through [LM Studio](https://lmstudio.ai/). No account, no cloud, nothing stored.

## Features (current state)

| Requirement | Status |
|---|---|
| Upload a `.txt` Panopto transcript or paste text (FR1, UR2) | ✅ |
| File validation and clear error messages (FR5, FR8, UR11) | ✅ |
| Cleans timestamps / caption numbers automatically (FR2) | ✅ |
| Long transcripts via chunked map-reduce summarization (FR11, UR3) | ✅ first version |
| Short / Medium / Detailed summaries, Medium by default (FR14, FR15) | ✅ |
| Main topics + action items sections (UR5, FR7) | ✅ |
| Choice of summary language (FR10) | ✅ |
| Speaker labels detected and passed to the model (FR16) | ✅ first version |
| Copy to clipboard, download `.txt` / `.docx` (UR7, FR4) | ✅ |
| Link back to the original Panopto lecture (UR9) | ✅ when the link is in the file |
| AI disclaimer (NFR12) | ✅ |
| Evaluation with an LLM judge (AI requirements) | ⏳ planned |

## Tech stack

- **Python 3.11+**
- **Streamlit** for the local web UI
- **LM Studio** local server (OpenAI-compatible API on `http://localhost:1234/v1`)
- Suggested models: `Qwen2.5-7B-Instruct` or `Llama-3.1-8B-Instruct` (Q4_K_M GGUF, about 5 GB, runs on 16 GB RAM laptops)
- **python-docx** for Word export

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

1. Install LM Studio, download one of the models above and load it.
2. In LM Studio open the **Developer** tab and click **Start Server**.
3. Run the app:

```bash
streamlit run app.py
```

Try it with `samples/sample_transcript.txt`.

All tunable settings (model name, chunk size, temperature, detail levels, languages) are in [`config.py`](config.py).

## Project structure

```
app.py                  Streamlit UI
config.py               All parameters in one place
summarizer/
  transcript.py         Load, validate, clean Panopto transcripts
  chunking.py           Split long transcripts into overlapping chunks
  llm_client.py         Talks to the LM Studio local server
  summarize.py          Prompting and map-reduce summarization
  export.py             .txt and .docx export
samples/                Example transcript (fake data)
docs/                   Sprint plan and project-management notes
```

## Branches

| Branch | Purpose |
|---|---|
| `main` | Stable, working version. Only updated through reviewed pull requests at the end of a sprint. |
| `develop` | Integration branch. Finished features are merged here first and tested together. |
| `feature/<name>` | One branch per board task (for example `feature/transcript-processing`, `feature/llm-summarizer`, `feature/export`). Branch off `develop`, open a PR back into `develop`. |

## Privacy

Transcripts and summaries are only held in memory while the app is open. Nothing is sent to external servers, and `transcripts/` is git-ignored so real lecture data is never committed.
