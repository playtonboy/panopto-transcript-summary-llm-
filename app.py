"""Streamlit user interface: upload/paste -> generate -> view/copy/download (UR12).

Run with:  streamlit run app.py
Nothing is written to disk and no account is needed (FR3, NFR3).
"""

import html

import streamlit as st
import streamlit.components.v1 as components

import config
from summarizer import export, llm_client
from summarizer.summarize import summarize
from summarizer.transcript import TranscriptError, decode, parse, validate_upload

st.set_page_config(page_title="Lecture Summarizer", page_icon="📝", layout="centered")
st.title("📝 Panopto Lecture Summarizer")
st.caption("Runs entirely on your computer with LM Studio. Your transcript never leaves this machine.")

if not llm_client.is_server_running():
    st.warning("LM Studio server not detected at " + config.LMSTUDIO_BASE_URL + ". Start it before generating.")

upload_tab, paste_tab = st.tabs(["Upload transcript", "Paste text"])
with upload_tab:
    uploaded = st.file_uploader("Panopto transcript (.txt)", type=[e.lstrip(".") for e in config.ALLOWED_EXTENSIONS])
with paste_tab:
    pasted = st.text_area("Transcript text", height=200)

col1, col2 = st.columns(2)
with col1:
    detail = st.radio(
        "Detail level",
        list(config.DETAIL_LEVELS),
        index=list(config.DETAIL_LEVELS).index(config.DEFAULT_DETAIL_LEVEL),
        horizontal=True,
    )
with col2:
    language = st.selectbox(
        "Summary language",
        config.OUTPUT_LANGUAGES,
        index=config.OUTPUT_LANGUAGES.index(config.DEFAULT_OUTPUT_LANGUAGE),
    )
custom_title = st.text_input("Custom title (optional)")

if st.button("Generate summary", type="primary"):
    try:
        if uploaded is not None:
            validate_upload(uploaded.name, uploaded.size)
            raw = decode(uploaded.getvalue())
        elif pasted.strip():
            raw = pasted
        else:
            raise TranscriptError("Please upload a transcript or paste its text first.")
        transcript = parse(raw)

        progress = st.progress(0.0, text="Starting...")
        st.session_state.summary = summarize(
            transcript,
            detail_level=detail,
            language=language,
            title=custom_title.strip() or None,
            on_progress=lambda message, fraction: progress.progress(fraction, text=message),
        )
    except (TranscriptError, llm_client.LLMError) as error:
        st.error(str(error))

summary = st.session_state.get("summary")
if summary:
    st.divider()
    st.subheader(summary.title)
    st.markdown(summary.body)
    if summary.source_url:
        st.markdown(f"[Original lecture]({summary.source_url})")
    st.caption(summary.disclaimer)

    c1, c2, c3 = st.columns(3)
    with c1:
        # One-click copy (UR7). Streamlit has no clipboard API, so use a tiny HTML button.
        # The summary is model output, so it is HTML-escaped into a hidden textarea.
        embed = getattr(st, "iframe", None) or components.html
        embed(
            f"""<textarea id="s" hidden>{html.escape(summary.as_text())}</textarea>
            <button onclick="navigator.clipboard.writeText(document.getElementById('s').value)"
            style="padding:.45rem .9rem;border-radius:.5rem;border:1px solid #ccc;cursor:pointer">
            📋 Copy</button>""",
            height=48,
        )
    with c2:
        st.download_button("Download .txt", export.to_txt(summary), file_name="summary.txt", mime="text/plain")
    with c3:
        st.download_button(
            "Download .docx",
            export.to_docx(summary),
            file_name="summary.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
