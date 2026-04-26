"""e2e (real Claude Code): dummy A/B/C concurrent scenario per #5 § 3.X.

Spawns three real `claude` processes on throwaway projects under a
tmpdir HOME, drives them through IDLE → ASKING → BUSY → IDLE in
staggered timing, and asserts the classifier observes the transitions.

**Cost**: each run consumes Claude API tokens (3 sessions × multiple
turns each). The test is gated behind `CLAUDE_E2E_REAL=1` so a default
`make test-e2e` invocation never hits the wallet.

**Status**: structural skeleton in place. The pexpect interaction with
Claude Code's TUI (approval-modal keystroke, prompt-ready detection,
session settle timing) needs one iteration cycle on a live `claude`
binary before the assertions can be made tight. Marked `xfail` /
`skip` accordingly until that lands. See § 3.1 of the closure devlog.
"""

import os
import shutil
import threading
import time
from pathlib import Path

import pytest

from claude_busy_monitor import ClaudeState, get_sessions

pexpect = pytest.importorskip("pexpect", reason="pexpect required for real-CC e2e")

REAL_E2E_ENABLED = os.environ.get("CLAUDE_E2E_REAL") == "1"
CLAUDE_AVAILABLE = shutil.which("claude") is not None

pytestmark = [
    pytest.mark.skipif(
        not REAL_E2E_ENABLED,
        reason="CLAUDE_E2E_REAL=1 required (this test consumes Claude API tokens)",
    ),
    pytest.mark.skipif(not CLAUDE_AVAILABLE, reason="`claude` binary not on PATH"),
]


def _spawn_dummy(name: str, home: Path):
    """Spawn one `claude` process inside a throwaway project under HOME."""
    project = home / "projects" / name
    project.mkdir(parents=True)
    env = {**os.environ, "HOME": str(home)}
    return pexpect.spawn(
        "claude",
        cwd=str(project),
        env=env,
        encoding="utf-8",
        timeout=60,
    )


def _drive_dummy(child, label: str) -> None:
    """Drive one dummy through the IDLE → ASKING → BUSY → IDLE timeline.

    NOTE: keystrokes here are placeholders — Claude Code's approval-modal
    accepts `1` (yes, once) on its own line, and the prompt-ready cue is
    a TUI repaint of `>`. Both need one iteration cycle on a live binary
    before this can be tightened. For now: timing-based, no expects.
    """
    time.sleep(2)  # IDLE window
    child.sendline("Run `pwd` via Bash, then say done")
    time.sleep(2)  # ASKING window (approval modal)
    child.sendline("1")  # approve
    time.sleep(1)  # BUSY (pwd is fast)
    child.sendline("Now run `sleep 10 && echo done` via Bash")
    time.sleep(2)  # ASKING again
    child.sendline("1")  # approve
    time.sleep(11)  # BUSY for ~10s


@pytest.mark.xfail(reason="Real CC keystroke + TUI sync details pending one iteration cycle")
def test_classifier_observes_dummy_a_b_c_concurrent(isolated_home):
    """Per #5 § 3.X: A starts now; B starts +5s; C starts +10s. Assert states."""
    children = {}
    threads = []

    def start_after(label: str, delay: float):
        time.sleep(delay)
        children[label] = _spawn_dummy(label, isolated_home)
        _drive_dummy(children[label], label)

    for label, delay in [("A", 0.0), ("B", 5.0), ("C", 10.0)]:
        t = threading.Thread(target=start_after, args=(label, delay), daemon=True)
        t.start()
        threads.append(t)

    # Sample classifier state across the timeline.
    samples: list[dict] = []
    deadline = time.monotonic() + 35.0
    while time.monotonic() < deadline:
        sessions = get_sessions()
        samples.append({s.name: s.state for s in sessions})
        time.sleep(1.0)

    # Drain threads.
    for t in threads:
        t.join(timeout=10.0)

    # Tear down children.
    for child in children.values():
        try:
            child.sendline("/exit")
            child.expect(pexpect.EOF, timeout=5)
        except pexpect.exceptions.TIMEOUT:
            child.terminate(force=True)

    # Assertions to tighten in the next iteration:
    # 1. At some sample, all three sessions visible.
    # 2. Each session passes through BUSY at least once.
    # 3. End-of-timeline sample shows zero live sessions (all torn down).
    assert any(len(s) == 3 for s in samples), "never saw 3 concurrent sessions"
    states_seen = {state for sample in samples for state in sample.values()}
    assert ClaudeState.BUSY in states_seen
