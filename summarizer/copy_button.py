"""A "Copy summary" button for the Streamlit page."""

import html

import streamlit as st
import streamlit.components.v1 as components


def copy_button_html(text: str, label: str = "Copy summary") -> str:
    """Return a small HTML button that copies `text` to the clipboard."""
    safe_text = html.escape(text)
    safe_label = html.escape(label)
    return f"""
<textarea id="copy-source" style="display:none">{safe_text}</textarea>
<button id="copy-btn">{safe_label}</button>
<script>
document.getElementById("copy-btn").addEventListener("click", async () => {{
  const btn = document.getElementById("copy-btn");
  const text = document.getElementById("copy-source").value;
  try {{
    await navigator.clipboard.writeText(text);
    btn.innerText = "Copied!";
  }} catch (err) {{
    btn.innerText = "Copy failed";
  }}
}});
</script>
"""


def show_copy_button(text: str, label: str = "Copy summary") -> None:
    """Show the copy button in the Streamlit app."""
    button = copy_button_html(text, label)
    if hasattr(st, "iframe"):  # newer Streamlit: components.html is deprecated and will be removed
        st.iframe(button, height=50)
    else:
        components.html(button, height=50)