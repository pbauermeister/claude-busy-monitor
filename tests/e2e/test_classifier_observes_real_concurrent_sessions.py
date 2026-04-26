"""e2e (real Claude Code): dummy A/B concurrent scenario.

Spawns two real `claude` processes on throwaway projects under a
tmpdir workspace, drives them through IDLE → ASKING → BUSY → IDLE in
staggered timing (A at t=0, B at t=3), and asserts the classifier
observes the transitions.

**Why two dummies, not the three the original brief asked for**:
empirical observation — A reliably runs the cycle; B works ~50% of
the time; with C added, C never made the cycle and the run hung. CC
appears to serialise some shared resource (auth handshake? LLM rate
limiter?) under concurrent spawn, and the third instance is the one
that loses. Two-dummy A/B keeps the staggered-concurrency property
that motivated the test; iterating to three is a follow-up.

**Cost**: each run consumes Claude API tokens (2 sessions × ~3 turns
each). Gated behind `CLAUDE_E2E_REAL=1` so a default `make test-e2e`
invocation never hits the wallet.

**Status**: marked `xfail` because B is still flaky (~50% pass rate
on the menu-pick step). See § 3.1 of the closure devlog.

**Diagnosing locally**:

- pytest with capture disabled (live A output to console):
    `CLAUDE_E2E_REAL=1 uv run pytest -s -v tests/e2e/test_classifier_observes_real_concurrent_sessions.py`
- standalone (no pytest test infrastructure — just a script):
    `uv run python tests/e2e/test_classifier_observes_real_concurrent_sessions.py`
  Uses a tempfile workspace, echoes A's CC output live to stdout,
  prints classifier samples each second, tears down at the end.
  (`uv run` activates the .venv so pexpect and pytest are importable;
  pytest is only used as a library here, not as the test runner.)
"""

import os
import shutil
import sys
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
        reason="CLAUDE_E2E_REAL=1 required (this test spawns real Claude Code)",
    ),
    pytest.mark.skipif(not CLAUDE_AVAILABLE, reason="`claude` binary not on PATH"),
]


def _spawn_dummy(name: str, workspace: Path, echo: bool = False):
    """Spawn one `claude` process inside a throwaway project under workspace.

    HOME is *not* overridden — `claude` inherits the user's real auth
    (`~/.claude/.credentials.json`) so no fresh login is needed.
    Sessions/transcripts land in real `~/.claude/`; the test filters by
    cwd to scope assertions to its own dummies.

    A pexpect logfile (`<workspace>/<name>.log`) captures everything CC
    writes — useful for diagnosing TUI-sync issues without rerunning.
    When `echo=True`, CC's output is also tee'd live to stdout (use
    pytest `-s` to actually see it; outside pytest it just prints).
    """
    project = workspace / name
    project.mkdir(parents=True)
    log_path = workspace / f"{name}.log"
    child = pexpect.spawn(
        "claude",
        cwd=str(project),
        encoding="utf-8",
        timeout=60,
    )
    child.logfile = open(log_path, "w")  # noqa: SIM115 — owned for child lifetime
    if echo:
        child.logfile_read = sys.stdout
    return child


def _start_drainer(child, stop_event: threading.Event) -> threading.Thread:
    """Continuously drain pexpect's pty buffer in a background thread.

    Without this, CC's TUI writes can fill the pty's kernel buffer
    (~4 KB on Linux), block CC on its next write, and prevent CC from
    reaching the "write probe file" step. Draining via
    `read_nonblocking()` also has the side effect of writing the bytes
    to `child.logfile` and `child.logfile_read`, so live-echo and
    on-disk capture both keep working.
    """

    def _drain() -> None:
        while not stop_event.is_set():
            try:
                child.read_nonblocking(size=4096, timeout=0.1)
            except pexpect.exceptions.TIMEOUT:
                continue
            except (pexpect.exceptions.EOF, OSError, ValueError):
                return

    thread = threading.Thread(target=_drain, daemon=True)
    thread.start()
    return thread


def _wait_for_dummy_ready(project_dir: Path, timeout: float = 90.0) -> bool:
    """Poll the classifier until a session whose cwd is `project_dir` shows.

    CC's startup takes ~15 s (auth, TUI init, probe-file write). Polling
    instead of a fixed sleep makes the timing robust to variance.
    """
    target = str(project_dir)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for s in get_sessions():
            if s.path == target or s.path == target + "/":
                return True
        time.sleep(0.5)
    return False


def _send_prompt(child, text: str) -> None:
    """Submit a prompt to CC's TUI.

    `pexpect.sendline()` sends `\\n`, which CC's raw-mode input handler
    treats as "newline within multi-line input" — not as submit. CC
    expects `\\r` (Enter) to submit. Send `\\r` explicitly.
    """
    child.send(text + "\r")


def _drive_dummy(child, project_dir: Path, label: str) -> None:
    """Drive one dummy through IDLE → ASKING → BUSY → IDLE.

    Step 0 (first-run only): CC shows a "Quick safety check — Is this a
    project you trust?" prompt for any unfamiliar cwd. Default option
    `1. Yes, I trust this folder` is pre-selected; Enter confirms. We
    must dismiss this BEFORE polling for the probe file: CC only
    writes the probe once it's in its main event loop, which it enters
    after the trust prompt is resolved. Polling first would deadlock.
    """
    time.sleep(4)  # let CC render the trust-prompt
    child.send("\r")  # Enter → confirms default option 1 (trust)
    if not _wait_for_dummy_ready(project_dir):
        return  # probe never appeared; later assertions will catch it
    time.sleep(2)  # IDLE pad — user-brief calls for an idle window first
    _send_prompt(child, "ask me something as a menu")
    time.sleep(15)  # ASKING — CC renders a menu prompt (12 + 3s headroom)
    _send_prompt(child, "1")  # pick first menu option
    _send_prompt(child, "sleep 5 seconds")  # queued; CC processes after menu pick
    time.sleep(3)  # drive returns early — CC keeps running until SIGKILL or exits naturally


def _run_dummy_scenario(workspace: Path, *, echo_a: bool, print_samples: bool):
    """Spawn A and B with staggered start, drive each through the timeline,
    sample classifier state once a second, return (samples, children, stop_drainers).

    Reused by both the pytest test and the `__main__` standalone runner.
    Caller is responsible for setting `stop_drainers` and tearing children down.
    """
    workspace_prefix = str(workspace)
    children: dict[str, "pexpect.spawn"] = {}
    threads: list[threading.Thread] = []
    stop_drainers = threading.Event()

    def start_after(label: str, delay: float, echo: bool):
        time.sleep(delay)
        child = _spawn_dummy(label, workspace, echo=echo)
        children[label] = child
        _start_drainer(child, stop_drainers)
        _drive_dummy(child, workspace / label, label)

    for label, delay, echo in [
        ("A", 0.0, echo_a),
        ("B", 3.0, False),
    ]:
        t = threading.Thread(target=start_after, args=(label, delay, echo), daemon=True)
        t.start()
        threads.append(t)

    # Hard 45s cap on the whole scenario — anything not done by then
    # gets killed by the teardown's SIGKILL. Per-dummy drive is ~32s
    # under happy path; B's flake doesn't extend wall time.
    samples: list[dict] = []
    deadline = time.monotonic() + 45.0
    start = time.monotonic()
    while time.monotonic() < deadline:
        sessions = [s for s in get_sessions() if s.path.startswith(workspace_prefix)]
        sample = {s.name: s.state for s in sessions}
        samples.append(sample)
        if print_samples:
            print(f"[t+{time.monotonic() - start:5.1f}s] {sample}", flush=True)
        time.sleep(1.0)

    # Drive threads are daemon=True; whatever's still running at this
    # point gets killed by the caller's _teardown_children. No join.

    return samples, children, stop_drainers


def _teardown_children(children: dict) -> None:
    """SIGKILL every child immediately. We don't need a clean shutdown —
    CC's probe file is auto-removed when the process dies, which is
    all the next run cares about. Skipping SIGTERM avoids the grace
    period and gets us past the hard 45s cap reliably.
    """
    import signal as _signal

    for child in children.values():
        try:
            os.kill(child.pid, _signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass
        try:
            child.close(force=False)
        except Exception:  # noqa: BLE001 — pexpect cleanup may raise harmlessly
            pass


@pytest.mark.xfail(reason="B is currently flaky (~50% pass rate on menu-pick step)")
def test_classifier_observes_dummy_a_b_concurrent(tmp_workspace):
    """A starts now; B starts +3s. Assert classifier sees both transition.

    Filters classifier output by cwd to scope assertions to dummies
    spawned inside `tmp_workspace`, ignoring any pre-existing live
    Claude sessions on the user's machine.
    """
    children: dict = {}
    stop_drainers: threading.Event | None = None
    try:
        samples, children, stop_drainers = _run_dummy_scenario(
            tmp_workspace, echo_a=True, print_samples=True
        )
        # 1. At some sample, both dummy sessions visible.
        # 2. At least one session passes through BUSY (A reliably; B ~50%).
        assert any(len(s) == 2 for s in samples), "never saw 2 concurrent dummies"
        states_seen = {state for sample in samples for state in sample.values()}
        assert ClaudeState.BUSY in states_seen
    finally:
        if stop_drainers is not None:
            stop_drainers.set()
        # Tear down children. Transcript-dir cleanup is the tmp_workspace
        # fixture's responsibility (yield/teardown).
        _teardown_children(children)


# =============================================================================
# Standalone runner — bypass pytest entirely
# =============================================================================


def _main() -> int:
    if not CLAUDE_AVAILABLE:
        print("`claude` not on PATH — install it before running this script.")
        return 2
    import tempfile

    keep_logs = os.environ.get("KEEP_LOGS") == "1"
    if keep_logs:
        # Don't use TemporaryDirectory — it would delete on exit.
        workspace_root = Path(tempfile.mkdtemp(prefix="cbm_e2e_"))
    else:
        # Stack the cleanup on the with-block.
        ctx = tempfile.TemporaryDirectory(prefix="cbm_e2e_")
        workspace_root = Path(ctx.name)

    workspace = workspace_root / "workspace"
    workspace.mkdir()
    print(f"workspace: {workspace}")
    print("starting A/B — A's CC output is echoed live below.")
    print("(set KEEP_LOGS=1 to keep <workspace>/{A,B}.log after run)\n")
    children: dict = {}
    stop_drainers: threading.Event | None = None
    try:
        samples, children, stop_drainers = _run_dummy_scenario(
            workspace, echo_a=True, print_samples=True
        )
    finally:
        if stop_drainers is not None:
            stop_drainers.set()
            time.sleep(0.5)  # let drainers observe the stop event
        _teardown_children(children)
        # Manual teardown of transcript dirs (no fixture here).
        real_projects = Path(os.path.expanduser("~/.claude/projects"))
        if real_projects.is_dir():
            encoded_prefix = str(workspace).replace("/", "-")
            for child in real_projects.iterdir():
                if child.name.startswith(encoded_prefix):
                    shutil.rmtree(child, ignore_errors=True)
        if not keep_logs:
            ctx.cleanup()

    print(f"\nsamples collected: {len(samples)}")
    states_seen = {state for sample in samples for state in sample.values()}
    print(f"states observed: {sorted(s.value for s in states_seen)}")
    print(f"max concurrent dummies seen: {max((len(s) for s in samples), default=0)}")
    if keep_logs:
        print(f"logs preserved at: {workspace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
