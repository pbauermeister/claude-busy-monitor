"""Smoke tests: `_is_process_claude` recognises both Claude Code launch forms.

Seed: #23. Spawns throwaway `sleep` copies so `/proc/<pid>/comm` and
`/proc/<pid>/exe` take realistic values — no real Claude Code needed.

- Launcher form: comm is literally "claude".
- Versioned-binary form (background jobs): comm is the version string;
  the exe lives at `.../claude/versions/<ver>`.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from claude_busy_monitor._sessions import _is_process_claude


@pytest.fixture
def spawn(tmp_path):
    """Return a helper that copies `sleep` to `rel` under tmpdir and runs it."""
    procs: list[subprocess.Popen] = []
    sleep = shutil.which("sleep")
    assert sleep, "sleep binary required"

    def _spawn(rel: str) -> subprocess.Popen:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(sleep, target)
        proc = subprocess.Popen([str(target), "30"])
        procs.append(proc)
        return proc

    yield _spawn
    for proc in procs:
        proc.kill()
        proc.wait()


def test_process_identity_accepts_launcher_form(spawn):
    proc = spawn("bin/claude")
    assert _is_process_claude(proc.pid)


def test_process_identity_accepts_versioned_binary_form(spawn):
    # Regression for #23: background jobs exec `.../claude/versions/2.1.289`
    # directly, so comm is "2.1.289" — previously dropped as "not claude".
    proc = spawn("share/claude/versions/2.1.289")
    assert Path(f"/proc/{proc.pid}/comm").read_text().strip() == "2.1.289"
    assert _is_process_claude(proc.pid)


def test_process_identity_rejects_unrelated_process(spawn):
    proc = spawn("bin/2.1.289")  # version-like name, but not under claude/versions
    assert not _is_process_claude(proc.pid)


def test_process_identity_rejects_dead_pid(spawn):
    proc = spawn("bin/claude")
    proc.kill()
    proc.wait()
    assert not _is_process_claude(proc.pid)
