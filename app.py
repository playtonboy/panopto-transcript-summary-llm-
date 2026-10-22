import streamlit as st

from summarizer.upload_validation import TranscriptError, validate_upload, decode

st.title("Panopto Transcript Summarizer")

uploaded_file = st.file_uploader(
    "Upload your transcript",
    type=["txt"]
)

if uploaded_file is not None:
    try:
        validate_upload(uploaded_file.name, uploaded_file.size)
        transcript_text = decode(uploaded_file.getvalue())

        st.success("Transcript uploaded successfully!")
        st.text_area("Transcript preview", transcript_text, height=250)

    except TranscriptError as error:
        st.error(str(error))