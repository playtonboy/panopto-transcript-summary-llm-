"""Tests for scripts/start_helper.py, used by start.sh and start.bat (SCRUM-14)."""

import socket
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import start_helper  # noqa: E402
from fake_lmstudio import start_fake_server  # noqa: E402


@pytest.fixture
def server():
    server, url = start_fake_server()
    yield url
    server.shutdown()


def free_port_url() -> str:
    with socket.socket() as s:  # nothing listens on this port after the with-block
        s.bind(("127.0.0.1", 0))
        return f"http://127.0.0.1:{s.getsockname()[1]}/v1"


def test_requirements_are_installed_again_only_when_they_change(tmp_path, monkeypatch):
    monkeypatch.setattr(start_helper, "STAMP", tmp_path / "requirements.sha256")
    assert start_helper.main(["deps-changed"]) == 0  # first start: install
    start_helper.main(["deps-saved"])
    assert start_helper.main(["deps-changed"]) == 1  # nothing changed: skip
    monkeypatch.setattr(start_helper, "requirements_hash", lambda: "something new")
    assert start_helper.main(["deps-changed"]) == 0  # requirements.txt changed: install again


def test_is_up_and_wait(server):
    assert start_helper.main(["is-up", server + "/models"]) == 0
    assert start_helper.main(["wait", server + "/models", "5"]) == 0
    assert start_helper.main(["is-up", free_port_url() + "/models"]) == 1
    assert start_helper.main(["wait", free_port_url() + "/models", "1"]) == 1


def test_lm_studio_warning_only_when_it_is_not_running(server, monkeypatch, capsys):
    monkeypatch.setattr(start_helper.config, "LMSTUDIO_BASE_URL", server)
    assert start_helper.main(["check-lmstudio"]) == 0
    assert capsys.readouterr().out == ""

    monkeypatch.setattr(start_helper.config, "LMSTUDIO_BASE_URL", free_port_url())
    assert start_helper.main(["check-lmstudio"]) == 0  # a warning, never a crash
    assert "LM Studio is not running" in capsys.readouterr().out


def test_open_waits_for_the_app_then_opens_the_browser(server, monkeypatch):
    opened = []
    monkeypatch.setattr(start_helper.webbrowser, "open", opened.append)
    assert start_helper.main(["open", server + "/models", "5"]) == 0
    assert opened == [server + "/models"]


def test_unknown_command_prints_help():
    assert start_helper.main(["nonsense"]) == 2


def test_start_scripts_exist_with_the_right_line_endings():
    assert b"\r\n" not in (ROOT / "start.sh").read_bytes()  # CRLF would break bash on macOS / Git Bash
    attributes = (ROOT / ".gitattributes").read_text()
    assert "*.sh  text eol=lf" in attributes and "*.bat text eol=crlf" in attributes
