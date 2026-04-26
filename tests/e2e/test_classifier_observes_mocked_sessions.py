"""e2e (mocked): classifier reads three concurrent fake sessions.

Seed: #3 § 3.7 item 11 — tmpdir tree mocking `~/.claude/sessions/<pid>.json`
+ `~/.claude/projects/<encoded>/<sid>.jsonl` exercises the full classifier
stack without spawning a real `claude` process.

This is the fast/free e2e — it runs by default. The slow/paid variant
(real Claude Code, dummy A/B/C scenario per #5 § 3.X) is in
`test_classifier_observes_real_concurrent_sessions.py` and is gated
behind the `CLAUDE_E2E_REAL=1` env var.
"""

import json

import pytest

from claude_busy_monitor import (
    ClaudeState,
    get_sessions,
    get_state_counts,
)


@pytest.fixture(autouse=True)
def claude_pid_always_valid(monkeypatch):
    monkeypatch.setattr("claude_busy_monitor._sessions._is_process_claude", lambda pid: True)


def _write_probe(sessions_dir, pid: int, cwd: str, sid: str, status: str) -> None:
    (sessions_dir / f"{pid}.json").write_text(
        json.dumps({"pid": pid, "cwd": cwd, "sessionId": sid, "status": status})
    )


def _write_transcript(projects_dir, cwd: str, sid: str, entries: list[dict]) -> None:
    encoded = cwd.replace("/", "-")
    project = projects_dir / encoded
    project.mkdir(parents=True, exist_ok=True)
    (project / f"{sid}.jsonl").write_text("\n".join(json.dumps(e) for e in entries))


def test_classifier_observes_three_concurrent_sessions_in_distinct_states(
    isolated_home,
):
    sessions_dir = isolated_home / ".claude" / "sessions"
    projects_dir = isolated_home / ".claude" / "projects"

    _write_probe(sessions_dir, 101, "/tmp/proj-a", "sid-a", "busy")
    _write_probe(sessions_dir, 102, "/tmp/proj-b", "sid-b", "waiting")
    _write_probe(sessions_dir, 103, "/tmp/proj-c", "sid-c", "idle")

    for cwd, sid in [
        ("/tmp/proj-a", "sid-a"),
        ("/tmp/proj-b", "sid-b"),
        ("/tmp/proj-c", "sid-c"),
    ]:
        _write_transcript(
            projects_dir,
            cwd,
            sid,
            [
                {
                    "type": "assistant",
                    "message": {"usage": {"input_tokens": 10, "output_tokens": 5}},
                }
            ],
        )

    sessions = get_sessions()
    counts = get_state_counts(sessions)

    assert len(sessions) == 3
    assert counts == {
        ClaudeState.BUSY: 1,
        ClaudeState.ASKING: 1,
        ClaudeState.IDLE: 1,
    }


def test_classifier_returns_empty_when_sessions_dir_is_empty(isolated_home):
    sessions = get_sessions()
    assert sessions == []
    assert get_state_counts(sessions) == {
        ClaudeState.BUSY: 0,
        ClaudeState.ASKING: 0,
        ClaudeState.IDLE: 0,
    }
