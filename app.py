"""Streamlit interface: upload or paste a transcript, generate a summary, export it."""

from dataclasses import replace
from pathlib import Path

import streamlit as st

import config
from interface import client
from summarizer import export
from summarizer.transcript import TranscriptError, parse
from summarizer.upload_validation import decode, validate_upload
from summarizer.copy_button import show_copy_button

st.set_page_config(page_title="Lecture Summarizer")
st.title("Panopto Lecture Summarizer")
st.caption("Runs entirely on your computer with LM Studio. Your transcript never leaves this machine.")



# Settings for this browser session only
with st.sidebar:
    st.header("Settings")

    orchestrator_url = st.text_input(
        "Summarizer service address",
        value=config.ORCHESTRATOR_URL,
        help="Only change this if you started the orchestrator on another port.",
    ).strip()

    if not client.is_local(orchestrator_url):
        st.error(
            "Only addresses on this computer (http://localhost:...) "
            "are allowed, so your transcript stays here."
        )
        orchestrator_url = config.ORCHESTRATOR_URL

    st.caption(
        f"AI model: chosen when you start a worker (default `{config.MODEL_NAME}`). "
        "Use another one with: `python -m worker.main --model <id>`"
    )

status = client.health(orchestrator_url)


if status is None:
    st.warning(
        "The summarizer service is not running. "
        "Start it with start.bat (Windows) or ./start.sh (macOS)."
    )
elif status.get("workers", 0) == 0:
    st.warning(
        "No AI worker is currently running. "
        "Your summary will wait until a worker becomes available."
    )
    
# Input: upload or paste
upload_tab, paste_tab = st.tabs(["Upload transcript", "Paste text"])
with upload_tab:
    uploaded_file = st.file_uploader("Panopto transcript (.txt)", type=["txt"])
    st.caption(
        "Where to find it: open the recording in Canvas, go to the Captions tab in the Panopto viewer "
        "and download the captions as a .txt file."
    )
with paste_tab:
    pasted_text = st.text_area("Transcript text", height=200)

# Options
detail = st.radio(
    "Detail level",
    list(config.DETAIL_LEVELS),
    index=list(config.DETAIL_LEVELS).index(config.DEFAULT_DETAIL_LEVEL),
    horizontal=True,
)

# Output language 
language = st.selectbox(
    "Summary language",
    config.OUTPUT_LANGUAGES,
    index=config.OUTPUT_LANGUAGES.index(config.DEFAULT_OUTPUT_LANGUAGE),
)

# Custom title. Empty -> the uploaded file's name without .txt.
custom_title = st.text_input("Summary title (optional)", placeholder="Leave empty to use the file name")

HISTORY_SIZE = 5


def summarize_now(transcript, source_title):
    """Send the transcript to the orchestrator, wait for the summary and keep it for this session."""
    progress = st.progress(0.0, text="Sending the transcript to the summarizer...")
    job_id = client.submit(transcript, detail_level=detail, language=language, url=orchestrator_url)
    summary = client.wait_for_summary(
        job_id,
        on_progress=lambda message, fraction: progress.progress(fraction, text=message),
        url=orchestrator_url,
    )
    st.session_state.default_title = source_title or summary.title
    st.session_state.summary = summary
    history = st.session_state.setdefault("history", [])
    history.insert(
        0, {"summary": replace(summary, title=st.session_state.default_title), "detail": detail, "language": language}
    )
    del history[HISTORY_SIZE:]


generate_column, regenerate_column = st.columns(2)
generate = generate_column.button("Generate summary", type="primary")
regenerate = regenerate_column.button(
    "Regenerate with these settings",
    disabled="transcript" not in st.session_state,
    help="Make a new summary of the same transcript, for example with another detail level or language.",
)

try:
    if generate:
        if uploaded_file is not None:
            validate_upload(uploaded_file.name, uploaded_file.size)
            raw = decode(uploaded_file.getvalue())
        elif pasted_text.strip():
            raw = pasted_text
        else:
            raise TranscriptError("Please upload a transcript or paste its text first.")
        # kept in memory only, so Regenerate does not need the file again
        st.session_state.transcript = parse(raw)
        st.session_state.source_title = Path(uploaded_file.name).stem if uploaded_file is not None else None
        summarize_now(st.session_state.transcript, st.session_state.source_title)
        st.session_state.enable_regenerate = True
    elif regenerate:
        summarize_now(st.session_state.transcript, st.session_state.source_title)
except (TranscriptError, client.JobFailed) as error:
    st.error(str(error))
except Exception:
    st.error("Something unexpected went wrong while processing your transcript. Please try again or check your file.")

if st.session_state.pop("enable_regenerate", False):
    st.rerun()

summary = st.session_state.get("summary")
if summary:
    summary.title = custom_title.strip() or st.session_state.get("default_title", summary.title)
    st.divider()
    st.subheader(summary.title)
    st.markdown(summary.body)
    st.caption(config.AI_DISCLAIMER)
    st.download_button("Download .txt", export.to_txt(summary), file_name="summary.txt", mime="text/plain")
    st.download_button(
        "Download .docx",
        export.to_docx(summary),
        file_name="summary.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    st.download_button("Download .pdf", export.to_pdf(summary), file_name="summary.pdf", mime="application/pdf")
    show_copy_button(summary.as_text(), "Copy summary to clipboard")

earlier = st.session_state.get("history", [])[1:]
if earlier:
    with st.expander(f"Earlier summaries in this session ({len(earlier)})"):
        for number, item in enumerate(earlier, start=1):
            st.markdown(f"**{number}. {item['summary'].title}** ({item['detail']}, {item['language']})")
            st.markdown(item["summary"].body)
            st.divider()