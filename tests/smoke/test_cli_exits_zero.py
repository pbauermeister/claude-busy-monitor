"""Smoke: CLI invocation exits 0 even on systems with no live Claude sessions.

Seed: #3 § 3.7 item 9. Verifies the CLI handles the empty / missing-dir
cases gracefully — `SESSIONS_DIR` not existing must not raise.
"""

import os
import subprocess
import sys


def _run_cli(env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "claude_busy_monitor._cli"],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_cli_exits_zero_when_sessions_dir_missing(tmp_path):
    env = {**os.environ, "HOME": str(tmp_path)}
    result = _run_cli(env)
    assert result.returncode == 0, result.stderr


def test_cli_exits_zero_when_sessions_dir_empty(tmp_path):
    sessions_dir = tmp_path / ".claude" / "sessions"
    sessions_dir.mkdir(parents=True)
    env = {**os.environ, "HOME": str(tmp_path)}
    result = _run_cli(env)
    assert result.returncode == 0, result.stderr


def test_cli_emits_summary_line_for_all_three_states(tmp_path):
    """Seed 10 (rendering invariant): summary line covers BUSY/ASKING/IDLE."""
    env = {**os.environ, "HOME": str(tmp_path)}
    result = _run_cli(env)
    assert result.returncode == 0, result.stderr
    assert "busy" in result.stdout
    assert "asking" in result.stdout
    assert "idle" in result.stdout
