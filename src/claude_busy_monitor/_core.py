"""Library core: classifier, probing, transcript reading, public API.

Strategy, schema assumptions, diagnostic recipes, and repair playbook
live in `README-STATE-DETECTION.md` at the repo root. **Read that
first** before changing the classifier or reacting to a misclassification
report — the assumptions there are reverse-engineered from undocumented
Claude Code internals and the README is the only place they're written
down. Inline references below are tagged `(see README §A1)` etc.

Public API exposed at the package root: `ClaudeState`, `TokenStats`,
`ClaudeSession`, `get_sessions()`, `get_state_counts()`.

Requires Claude Code v2.1.119+. Sessions from older versions (no `status`
field in their probe file) are silently dropped — exit them and resume
with `claude --resume <sessionId>` to migrate.
"""

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

SESSIONS_DIR = Path.home() / ".claude" / "sessions"
PROJECTS_DIR = Path.home() / ".claude" / "projects"


# =============================================================================
# Claude states and session
# =============================================================================


class ClaudeState(Enum):
    BUSY = "busy"
    ASKING = "asking"  # Awaiting user answer to a menu/dialog
    IDLE = "idle"  # Awaiting prompt

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TokenStats:
    """Cumulative token usage for a session."""

    output: int  # sum of assistant.message.usage.output_tokens
    input: int  # sum of input_tokens + cache_creation + cache_read


@dataclass(frozen=True)
class ClaudeSession:
    path: str  # absolute project home (cwd of the claude process)
    name: str  # last component of path
    id: str  # session id (stem of the active JSONL file), "" if unknown
    state: ClaudeState
    stats: TokenStats | None = None  # None if the jsonl is unreadable


# =============================================================================
# Probing — see README-STATE-DETECTION.md for the full design and assumptions
# =============================================================================


# Authoritative state mapping for the probe `status` field.
# Schema, repair playbook, and binary-side source of truth: README §A4.
_PROBE_STATUS_MAP: dict[str, ClaudeState] = {
    "busy": ClaudeState.BUSY,
    "idle": ClaudeState.IDLE,
    "waiting": ClaudeState.ASKING,
}


@dataclass
class _SessionProbe:
    pid: int
    cwd: str
    state: ClaudeState
    session_id_hint: str | None = None
    jsonl: Path | None = None


def _is_process_claude(pid: int) -> bool:
    # comm literal "claude" is the binary name. README §C if Claude Code
    # is ever renamed (every session would silently disappear from the listing).
    try:
        comm = Path(f"/proc/{pid}/comm").read_text().strip()
        if comm != "claude":
            return False
        return os.stat(f"/proc/{pid}").st_uid == os.getuid()
    except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
        return False


def _newest_jsonl(project_dir: Path) -> Path | None:
    best: Path | None = None
    best_mtime = -1.0
    for p in project_dir.glob("*.jsonl"):
        try:
            mt = p.stat().st_mtime
        except OSError:
            continue
        if mt > best_mtime:
            best_mtime = mt
            best = p
    return best


def _find_active_jsonl(
    cwd: str, session_id_hint: str | None, solo: bool
) -> Path | None:
    """Resolve a probe's live JSONL transcript (used for token stats only).

    Path encoding and the solo-vs-multi disambiguation: README §A2, §A3.
    """
    encoded = cwd.replace("/", "-")  # README §A2 if encoding ever changes
    project_dir = PROJECTS_DIR / encoded
    if not project_dir.is_dir():
        return None
    if solo:
        return _newest_jsonl(project_dir)
    if session_id_hint:
        candidate = project_dir / f"{session_id_hint}.jsonl"
        if candidate.is_file():
            return candidate
    return None


def _compute_token_stats(path: Path | None) -> TokenStats | None:
    """Tally cumulative token usage from a full jsonl transcript.

    Linear in file size; a 1 MB transcript is sub-millisecond.
    Field names and the cache-vs-fresh accounting: README §B.
    """
    if path is None:
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    output = 0
    input_total = 0
    for raw in data.splitlines():
        if not raw.strip():
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if obj.get("type") != "assistant":
            continue
        usage = (obj.get("message") or {}).get("usage")
        if not isinstance(usage, dict):
            continue
        output += int(usage.get("output_tokens") or 0)
        input_total += (
            int(usage.get("input_tokens") or 0)
            + int(usage.get("cache_creation_input_tokens") or 0)
            + int(usage.get("cache_read_input_tokens") or 0)
        )
    return TokenStats(output=output, input=input_total)


def _load_session_probes() -> list[_SessionProbe]:
    """Enumerate live claude sessions with state from their probe files.

    Probe file shape: README §A1. Status field semantics: README §A4.
    Probes without a recognized `status` field (older Claude Code) are
    dropped — migrate them by exiting and `claude --resume <sessionId>`.
    """
    if not SESSIONS_DIR.is_dir():
        return []
    probes: list[_SessionProbe] = []
    for entry in sorted(SESSIONS_DIR.glob("*.json")):
        try:
            data = json.loads(entry.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        pid = data.get("pid")
        cwd = data.get("cwd")
        session_id = data.get("sessionId")
        status = data.get("status")
        if not (isinstance(pid, int) and isinstance(cwd, str)):
            continue
        state = _PROBE_STATUS_MAP.get(status) if isinstance(status, str) else None
        if state is None:
            continue
        if not _is_process_claude(pid):
            continue
        probes.append(
            _SessionProbe(
                pid=pid,
                cwd=cwd,
                state=state,
                session_id_hint=session_id if isinstance(session_id, str) else None,
            )
        )
    return probes


# =============================================================================
# Public API
# =============================================================================


def get_sessions() -> list[ClaudeSession]:
    """Return live Claude sessions for the current user, with state.

    Non-blocking: single filesystem pass. Requires Claude Code v2.1.119+.
    """
    probes = _load_session_probes()
    if not probes:
        return []

    cwd_counts: dict[str, int] = {}
    for p in probes:
        cwd_counts[p.cwd] = cwd_counts.get(p.cwd, 0) + 1

    sessions: list[ClaudeSession] = []
    for p in probes:
        solo = cwd_counts[p.cwd] == 1
        p.jsonl = _find_active_jsonl(p.cwd, p.session_id_hint, solo)
        sid = p.jsonl.stem if p.jsonl is not None else (p.session_id_hint or "")
        sessions.append(
            ClaudeSession(
                path=p.cwd,
                name=os.path.basename(p.cwd.rstrip("/")),
                id=sid,
                state=p.state,
                stats=_compute_token_stats(p.jsonl),
            )
        )
    return sessions


def get_state_counts(
    sessions: list[ClaudeSession] | None = None,
) -> dict[ClaudeState, int]:
    """Count live sessions by state. All ClaudeState keys are present."""
    counts = {state: 0 for state in ClaudeState}
    for s in sessions or get_sessions():
        counts[s.state] += 1
    return counts
