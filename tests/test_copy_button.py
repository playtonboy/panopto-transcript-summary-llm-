"""The copy button (UR7) escapes the summary and uses st.iframe, because components.html is deprecated (SCRUM-13)."""

import streamlit
import streamlit.components.v1 as components

from summarizer import copy_button


def test_the_summary_text_is_escaped():
    page = copy_button.copy_button_html("<script>alert(1)</script> & more")
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt; &amp; more" in page


def test_the_button_uses_st_iframe_when_streamlit_has_it(monkeypatch):
    shown = []
    monkeypatch.setattr(streamlit, "iframe", lambda html, height: shown.append(("iframe", height)), raising=False)
    monkeypatch.setattr(components, "html", lambda html, height: shown.append(("components", height)))
    copy_button.show_copy_button("Summary")
    assert shown == [("iframe", 50)]


def test_older_streamlit_falls_back_to_components_html(monkeypatch):
    shown = []
    monkeypatch.delattr(streamlit, "iframe", raising=False)
    monkeypatch.setattr(components, "html", lambda html, height: shown.append(("components", height)))
    copy_button.show_copy_button("Summary")
    assert shown == [("components", 50)]
