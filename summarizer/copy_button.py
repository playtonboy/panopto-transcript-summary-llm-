import html

import streamlit.components.v1 as components


def copy_button_html(text: str, label: str = "Copy summary") -> str:
    """Return a small HTML button that copies `text` to the clipboard (UR7)."""
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
    components.html(copy_button_html(text, label), height=50)