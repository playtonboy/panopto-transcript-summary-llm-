"""Streamlit interface: upload or paste -> Generate -> summary on screen (UR12, FR6, FR13).

Run with:  streamlit run app.py
"""

import streamlit as st

import config
from summarizer import export, llm_client
from summarizer.summarize import summarize
from summarizer.transcript import TranscriptError, parse
from summarizer.upload_validation import decode, validate_upload
from summarizer.copy_button import show_copy_button

st.set_page_config(page_title="Lecture Summarizer")
st.title("Panopto Lecture Summarizer")
st.caption("Runs entirely on your computer with LM Studio. Your transcript never leaves this machine.")

if not llm_client.is_server_running():
    st.warning("LM Studio is not running. Open LM Studio, load the model and start the local server before generating.")

# Input: upload (SCRUM-46) or paste (SCRUM-35)
upload_tab, paste_tab = st.tabs(["Upload transcript", "Paste text"])
with upload_tab:
    uploaded_file = st.file_uploader("Panopto transcript (.txt)", type=["txt"])
with paste_tab:
    pasted_text = st.text_area("Transcript text", height=200)

# Options (SCRUM-23 will turn this into the final detail-level selector)
detail = st.radio(
    "Detail level",
    list(config.DETAIL_LEVELS),
    index=list(config.DETAIL_LEVELS).index(config.DEFAULT_DETAIL_LEVEL),
    horizontal=True,
)

if st.button("Generate summary", type="primary"):
    try:
        if uploaded_file is not None:
            validate_upload(uploaded_file.name, uploaded_file.size)
            raw = decode(uploaded_file.getvalue())
        elif pasted_text.strip():
            raw = pasted_text
        else:
            raise TranscriptError("Please upload a transcript or paste its text first.")
        transcript = parse(raw)

        progress = st.progress(0.0, text="Starting...")
        st.session_state.summary = summarize(
            transcript,
            detail_level=detail,
            on_progress=lambda message, fraction: progress.progress(fraction, text=message),
        )
    except (TranscriptError, llm_client.LLMError) as error:
        st.error(str(error))

    except Exception:
        st.error(
            "Something unexpected went wrong while processing your transcript. "
            "Please try again or check your file."
        )

# Result (FR6). Kept in session_state because Streamlit re-runs the script on every click.
summary = st.session_state.get("summary")
if summary:
    st.divider()
    st.subheader(summary.title)
    st.markdown(summary.body)
    if summary.source_url:
        st.markdown(f"[Original lecture]({summary.source_url})")
    st.caption(config.AI_DISCLAIMER)  # NFR12
    st.download_button("Download .txt", export.to_txt(summary), file_name="summary.txt", mime="text/plain")
    st.download_button(
        "Download .docx",
        export.to_docx(summary),
        file_name="summary.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    show_copy_button(summary.as_text(), "Copy summary")
