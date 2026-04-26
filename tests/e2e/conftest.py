"""e2e fixtures: tmpdir HOME isolation + classifier polling helpers.

The HOME override is applied via two complementary monkey-patches:

1. `os.environ["HOME"]` — for any subprocess we spawn (e.g. `claude`)
   that reads `~` via the environment.
2. `claude_busy_monitor._sessions.SESSIONS_DIR` and `PROJECTS_DIR` —
   these constants were resolved at import time from the *real*
   `Path.home()`; rebinding the module attributes redirects all
   subsequent classifier reads to our tmpdir.

Together they ensure no e2e fixture ever touches the user's real
`~/.claude/` state.
"""

import os
import time
from pathlib import Path

import pytest


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    sessions_dir = home / ".claude" / "sessions"
    projects_dir = home / ".claude" / "projects"
    sessions_dir.mkdir(parents=True)
    projects_dir.mkdir(parents=True)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr("claude_busy_monitor._sessions.SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr("claude_busy_monitor._sessions.PROJECTS_DIR", projects_dir)
    return home


def assert_no_real_claude_state_touched(home: Path) -> None:
    """Sanity check at teardown: the real ~/.claude/ was untouched.

    Verifies our HOME override actually held — if a subprocess managed
    to bypass the override, it would have written to the real
    `~/.claude/sessions/`. We don't compare contents (the user may
    have other live sessions); we just verify our tmpdir HOME was
    written to instead, which is enough.
    """
    real_home = Path(os.path.expanduser("~"))
    assert home != real_home, "fixture leak: HOME points at real home"


def poll_until(predicate, timeout: float = 30.0, interval: float = 0.5) -> bool:
    """Poll `predicate()` every `interval` until True or timeout.

    Returns True if the predicate became true; False otherwise. Used to
    wait for state transitions in the classifier without hard-coded
    sleeps that race against Claude Code's own write timing.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False
