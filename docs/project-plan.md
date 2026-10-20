# Project plan: Panopto Transcript Summary (local LLM)

> Owner names are placeholders (`Teammate 2-4`) until the team list is final. The instructor is added to the board as an observer/collaborator and has **no** implementation tasks.

## Scrum setup

- **Sprint length:** 1 week (Tuesday to Monday).
- **Stand-up:** 5 minutes every 2 days. Each person answers: what did I do, what will I do next, is anything blocking me.
- **Sprint planning:** at the start of each sprint (15 min), pick tasks from the backlog into the sprint.
- **Sprint review + retro:** at the end of each sprint (15 min). Merge `develop` into `main` via pull request if the increment works.
- **Board columns:** Backlog → To Do (this sprint) → In Progress → In Review (PR open) → Done.
- **Scrum master** rotates every sprint in team order; after the last person it starts again from the first.

## Sprint calendar and scrum master rotation

| Sprint | Dates | Scrum master | Stand-ups | Sprint goal |
|---|---|---|---|---|
| Sprint 1 | Tue 20 Oct - Mon 26 Oct 2026 | Platon | Thu 22 Oct, Sat 24 Oct, Mon 26 Oct (+ review) | Working end-to-end prototype: upload/paste → summary → view/copy/download |
| Sprint 2 | Tue 27 Oct - Mon 2 Nov 2026 | Teammate 2 | Thu 29 Oct, Sat 31 Oct, Mon 2 Nov (+ review) | Test on real 30-90 min lectures, consistency, languages, evaluation script |
| Sprint 3 | Tue 3 Nov - Mon 9 Nov 2026 | Teammate 3 | every 2 days | Robustness, start script, optional PDF |
| Sprint 4 | Tue 10 Nov - Mon 16 Nov 2026 | Teammate 4 | every 2 days | (to plan) |
| Sprint 5 | Tue 17 Nov - Mon 23 Nov 2026 | Platon (rotation restarts) | every 2 days | (to plan) |

## Task backlog

Estimates are in hours. Requirement IDs refer to the requirements document (v2).

| # | Task | Req. | Priority | Owner | Sprint | Est. (h) | Status | Implementation details |
|---|---|---|---|---|---|---|---|---|
| 1 | Set up GitHub repo, branches and README | - | High | Platon | Sprint 1 | 2 | Done | GitHub; branches main / develop / feature/*; Python 3.11+ venv; requirements.txt |
| 2 | Install LM Studio and pick a local model | NFR4, AI reqs | High | Teammate 2 | Sprint 1 | 4 | To Do | LM Studio local server (OpenAI-compatible API, localhost:1234). Compare Qwen2.5-7B-Instruct vs Llama-3.1-8B-Instruct (Q4_K_M GGUF, ~5 GB) on context length, speed and RAM on a 16 GB laptop |
| 3 | Transcript file upload and validation | FR1, FR5, FR8 | High | Teammate 3 | Sprint 1 | 3 | In Review | Streamlit st.file_uploader; accept .txt only, max 5 MB, reject empty files; summarizer/transcript.py validate_upload() |
| 4 | Paste-text input | UR2 | High | Teammate 3 | Sprint 1 | 1 | In Review | Streamlit st.text_area as second input tab |
| 5 | Clean Panopto transcript text | FR2, UR9, FR16 | High | Teammate 4 | Sprint 1 | 4 | In Review | Python regex: strip caption numbers and timestamps, decode UTF-8/UTF-16/Latin-1, extract title, Panopto URL and speaker labels; summarizer/transcript.py parse() |
| 6 | LM Studio client with error handling | NFR4, NFR10, UR11 | High | Teammate 2 | Sprint 1 | 3 | In Review | requests POST /v1/chat/completions; friendly errors for server not running, timeout, bad response; summarizer/llm_client.py |
| 7 | Chunk long transcripts (no cut-off) | FR11, UR3, NFR8 | High | Teammate 2 | Sprint 1 | 5 | In Review | Split at sentence boundaries into ~5000-token chunks with 200-token overlap (1 token ~ 4 chars); summarizer/chunking.py |
| 8 | Summarization prompts: topics, bullets, action items | FR18, UR4, UR5, FR7, NFR2 | High | Platon | Sprint 1 | 6 | In Review | Map-reduce prompting: notes per chunk, then final Markdown summary with Main topics / Summary / Action items; temperature 0.2; summarizer/summarize.py |
| 9 | Detail level selector with default | FR14, FR15, UR6 | Medium | Teammate 4 | Sprint 1 | 2 | In Review | Short=5 / Medium=10 / Detailed=15 bullets, Medium default; config.DETAIL_LEVELS |
| 10 | Streamlit UI flow with progress status | UR12, FR6, FR13 | High | Teammate 3 | Sprint 1 | 4 | In Review | Streamlit app.py: input tabs, options, Generate button, st.progress per chunk, on-screen preview |
| 11 | Export summary as .txt and .docx | FR4, NFR7, UR8 | High | Teammate 4 | Sprint 1 | 3 | In Review | In-memory export with python-docx; st.download_button; summarizer/export.py |
| 12 | One-click copy to clipboard | UR7 | Low | Teammate 3 | Sprint 1 | 1 | In Review | Small HTML button using navigator.clipboard (text HTML-escaped) |
| 13 | AI disclaimer and link to original lecture | NFR12, UR9 | Medium | Teammate 4 | Sprint 1 | 1 | In Review | Disclaimer text in config.AI_DISCLAIMER, appended to screen, .txt and .docx |
| 14 | Collect real Panopto transcripts for testing | FR2, UR3 | High | Platon | Sprint 2 | 3 | To Do | 3-5 own lectures of 30-90 min exported from Panopto; check export format against parser; keep them out of git (transcripts/ is ignored) |
| 15 | Long-transcript performance tuning | NFR1, UR10, NFR8 | High | Teammate 2 | Sprint 2 | 4 | To Do | Time 30/60/90-min transcripts; tune CHUNK_TOKENS and MODEL_CONTEXT_TOKENS in config.py; target < 2 min |
| 16 | Summary consistency check | FR12, NFR2 | High | Platon | Sprint 2 | 4 | To Do | Run same transcript 5x, compare bullet overlap; adjust temperature/prompt |
| 17 | LLM-as-judge evaluation script | AI reqs | High | Teammate 2 | Sprint 2 | 8 | To Do | Python script scoring each bullet from -1 to 1 for relevance using a larger model in LM Studio; output CSV of scores per lecture |
| 18 | Output language selection and translation check | FR10, NFR11 | Medium | Teammate 4 | Sprint 2 | 4 | To Do | Language dropdown already in UI; check Dutch/German output keeps academic terms; add languages to config.OUTPUT_LANGUAGES |
| 19 | Multilingual transcript input | FR9 | Medium | Teammate 4 | Sprint 2 | 3 | To Do | Test Dutch transcripts; prompt tells model to read any language and answer in the chosen one |
| 20 | Improve speaker identification | FR16 | Medium | Teammate 3 | Sprint 2 | 3 | To Do | Handle Panopto speaker formats; attribute key statements to speakers in summary |
| 21 | Custom summary title | FR17 | Low | Teammate 3 | Sprint 2 | 1 | In Review | Optional text input; used as heading in screen and exports |
| 22 | Edge cases and error messages | NFR9, UR11, FR8 | High | Teammate 3 | Sprint 2 | 2 | To Do | Empty, non-UTF-8, very large and non-transcript files must give a clear message and never crash |
| 23 | Privacy check: nothing stored or sent out | NFR3, NFR10, NFR4 | High | Teammate 4 | Sprint 2 | 2 | To Do | Verify no disk writes and only localhost network calls; document in README |
| 24 | One-click start script for non-technical users | UR12, NFR5 | Medium | Teammate 2 | Sprint 3 | 4 | To Do | start.bat / start.sh that creates venv, installs requirements and opens the app |
| 25 | PDF export (optional) | UR8 | Low | Teammate 4 | Sprint 3 | 3 | To Do | Only if time allows; e.g. fpdf2. FR4 (.txt/.docx) is the agreed scope, see requirements v2 |
| 26 | Update requirements document (v2) and keep v1 backup | - | Medium | Platon | Sprint 1 | 2 | Done | Changes listed in the Revision history section of v2 |

**Workload check (hours):** Sprint 1: Platon 8, Teammate 2 12, Teammate 3 9, Teammate 4 10. Sprint 2: Platon 7, Teammate 2 12, Teammate 3 6, Teammate 4 9.

## Overall technical design

- **Language:** Python 3.11+
- **UI:** Streamlit (local web page, no login)
- **Model runtime:** LM Studio local server, OpenAI-compatible REST API on `http://localhost:1234/v1`
- **Model:** a 7-8B instruct model in 4-bit GGUF (Qwen2.5-7B-Instruct or Llama-3.1-8B-Instruct), final choice in Sprint 1
- **Data:** Panopto transcript `.txt` exports (and pasted text). Kept in memory only, never stored or sent to external servers.
- **Long transcripts:** chunking + map-reduce summarization
- **Export:** `.txt` and `.docx` (python-docx)
- **Evaluation:** LLM-as-judge script rating each bullet from -1 to 1

## Importing the board

- **Jira:** Project settings → *Import issues* (or *Filters → Import issues from CSV*) → upload `jira-import.csv`. Map *Original Estimate* (seconds), *Sprint*, *Assignee* and *Labels*. Create Sprint 1 and Sprint 2 first so the sprint names match.
- **Trello:** Trello has no built-in CSV import. Create the lists *Backlog, To Do, In Progress, In Review, Done*, then paste the card names from `trello-cards.csv` into a list (Trello offers to create one card per line), or use a CSV import Power-Up.
