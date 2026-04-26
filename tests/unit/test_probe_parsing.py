"""Unit tests: probe-file parsing and validation in `_load_session_probes`.

Seed: #3 § 3.7 item 1.
"""

import json
from pathlib import Path

import pytest

from claude_busy_monitor import ClaudeState
from claude_busy_monitor._sessions import _load_session_probes


@pytest.fixture
def fake_sessions_dir(tmp_path, monkeypatch):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    monkeypatch.setattr("claude_busy_monitor._sessions.SESSIONS_DIR", sessions)
    return sessions


@pytest.fixture
def claude_pid_always_valid(monkeypatch):
    monkeypatch.setattr("claude_busy_monitor._sessions._is_process_claude", lambda pid: True)


def _write_probe(directory: Path, filename: str, body) -> None:
    payload = json.dumps(body) if isinstance(body, dict) else body
    (directory / filename).write_text(payload)


def test_probe_parsing_drops_malformed_json(fake_sessions_dir, claude_pid_always_valid):
    _write_probe(fake_sessions_dir, "1.json", "not-valid-json{")
    assert _load_session_probes() == []


def test_probe_parsing_drops_when_cwd_field_missing(fake_sessions_dir, claude_pid_always_valid):
    _write_probe(fake_sessions_dir, "1.json", {"pid": 123, "status": "busy"})
    assert _load_session_probes() == []


def test_probe_parsing_drops_when_pid_field_not_int(fake_sessions_dir, claude_pid_always_valid):
    _write_probe(
        fake_sessions_dir,
        "1.json",
        {"pid": "abc", "cwd": "/x", "status": "busy"},
    )
    assert _load_session_probes() == []


def test_probe_parsing_drops_unknown_status(fake_sessions_dir, claude_pid_always_valid):
    _write_probe(
        fake_sessions_dir,
        "1.json",
        {"pid": 123, "cwd": "/x", "status": "loading"},
    )
    assert _load_session_probes() == []


def test_probe_parsing_drops_missing_status(fake_sessions_dir, claude_pid_always_valid):
    _write_probe(fake_sessions_dir, "1.json", {"pid": 123, "cwd": "/x"})
    assert _load_session_probes() == []


def test_probe_parsing_drops_when_pid_is_not_claude(fake_sessions_dir, monkeypatch):
    monkeypatch.setattr("claude_busy_monitor._sessions._is_process_claude", lambda pid: False)
    _write_probe(
        fake_sessions_dir,
        "1.json",
        {"pid": 123, "cwd": "/x", "status": "busy"},
    )
    assert _load_session_probes() == []


def test_probe_parsing_accepts_valid_probe(fake_sessions_dir, claude_pid_always_valid):
    _write_probe(
        fake_sessions_dir,
        "1.json",
        {
            "pid": 123,
            "cwd": "/home/user/project",
            "sessionId": "abc-123",
            "status": "waiting",
        },
    )
    probes = _load_session_probes()
    assert len(probes) == 1
    assert probes[0].state == ClaudeState.ASKING
    assert probes[0].cwd == "/home/user/project"
    assert probes[0].session_id_hint == "abc-123"
