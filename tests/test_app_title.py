"""Tests for the custom summary title in app.py (SCRUM-41, FR17)."""

from streamlit.testing.v1 import AppTest

from summarizer.summarize import Summary


def run_app(custom_title: str = "") -> AppTest:
    at = AppTest.from_file("../app.py", default_timeout=30)
    # Pretend a summary was generated from the file "Lecture 5 - Testing.txt".
    at.session_state["summary"] = Summary(title="Lecture summary", body="## Summary\n- point")
    at.session_state["default_title"] = "Lecture 5 - Testing"
    at.run()
    if custom_title:
        at.text_input[0].input(custom_title).run()
    return at


def test_empty_title_field_uses_the_file_name():
    at = run_app()
    assert not at.exception
    assert at.subheader[0].value == "Lecture 5 - Testing"
    assert at.session_state["summary"].title == "Lecture 5 - Testing"


def test_typed_title_becomes_the_heading_and_is_used_for_downloads():
    at = run_app("My own title")
    assert at.subheader[0].value == "My own title"
    assert at.session_state["summary"].title == "My own title"


def test_no_original_lecture_link_on_screen():
    at = run_app()
    assert not any("Original lecture" in m.value for m in at.markdown)
