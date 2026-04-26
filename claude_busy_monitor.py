#!/usr/bin/env python3
"""List active Claude sessions for the current user with their state.

As a CLI, prints one tab-separated line per session: "<name>\t<id>\t<state>".

As a module, provides:
  - ClaudeState:          enum of possible session states
  - ClaudeSession:        dataclass describing one live session
  - get_sessions():       list[ClaudeSession] for all live claude processes
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

SESSIONS_DIR = Path.home() / ".claude" / "sessions"
PROJECTS_DIR = Path.home() / ".claude" / "projects"
TAIL_BYTES = 64 * 1024

_CLK_TCK = os.sysconf("SC_CLK_TCK")


# =============================================================================
# Claude states and session
# =============================================================================


class ClaudeState(Enum):
    BUSY = "busy"
    ASKING = "asking"  # Awaiting user answer to menu
    IDLE = "idle"  # Awaiting prompt

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TokenStats:
    """Cumulative token usage for a session, plus active compute time."""

    output: int  # sum of assistant.message.usage.output_tokens
    input_fresh: int  # sum of assistant.message.usage.input_tokens (uncached)
    input_cache_create: int  # sum of cache_creation_input_tokens
    input_cache_read: int  # sum of cache_read_input_tokens (cheap, cache hit)
    active_seconds: float  # sum of system/turn_duration.durationMs / 1000

    @property
    def input_total(self) -> int:
        """What the model actually saw (summing the three input categories)."""
        return self.input_fresh + self.input_cache_create + self.input_cache_read

    @property
    def throughput_tokens_per_s(self) -> float | None:
        """Output tokens per second of active (compute) time — model throughput."""
        if self.active_seconds <= 0:
            return None
        return self.output / self.active_seconds


@dataclass(frozen=True)
class ClaudeSession:
    path: str  # absolute project home (cwd of the claude process)
    name: str  # last component of path
    id: str  # session id (stem of the active JSONL file), "" if unknown
    state: ClaudeState
    stats: TokenStats | None = None  # None if the jsonl is unreadable


# =============================================================================
# ANSI colors
# =============================================================================

_ANSI_RESET = "\x1b[0m"

# Foregrounds
_FG_BLACK = "\x1b[30m"
_FG_WHITE = "\x1b[97m"
_FG_GREY = "\x1b[90m"

# Backgrounds
_BG_BLACK = "\x1b[40m"
_BG_RED = "\x1b[41m"
_BG_GREEN = "\x1b[42m"
_BG_YELLOW = "\x1b[43m"
_BG_BLUE = "\x1b[44m"
_BG_GREY = "\x1b[100m"

# Effects (ANSI blink applies to the foreground only)
_FX_BLINK = "\x1b[5m"
_FX_BOLD = "\x1b[1m"

_STATE_STYLE: dict[ClaudeState, str] = {
    ClaudeState.BUSY: _FG_BLACK + _BG_RED,
    ClaudeState.ASKING: _FG_BLACK + _BG_YELLOW + _FX_BLINK,
    ClaudeState.IDLE: _FG_BLACK + _BG_GREEN,
}


def _colorize(text: str, state: ClaudeState, doit: bool = True) -> str:
    """Wrap `text` in the ANSI style defined for `state`."""
    if not doit:
        return f"{_BG_BLACK}{_FG_GREY}{text}{_ANSI_RESET}"
    return f"{_STATE_STYLE[state]}{text}{_ANSI_RESET}"


# =============================================================================
# Probing
# =============================================================================
#
# -----------------------------------------------------------------------------
# STRATEGY — how we find ACTIVE sessions
# -----------------------------------------------------------------------------
# Two filesystem sources + /proc:
#
#   1. ~/.claude/sessions/<pid>.json
#        Each live `claude` process drops { pid, cwd, sessionId, ... } here.
#        ENUMERATION source. See `_load_session_probes`.
#
#   2. /proc/<pid>  (Linux only)
#        Verifies the candidate PID is still alive, has comm == "claude",
#        and is owned by the current UID. See `_is_process_claude`.
#
#   3. ~/.claude/projects/<encoded-cwd>/*.jsonl
#        The transcript. Resolved per-probe by `_find_active_jsonl`:
#          - solo probe for the cwd → newest jsonl (immune to /clear id
#            rotation that leaves sessions/<pid>.json stale);
#          - multiple concurrent probes for the same cwd → each uses its
#            own sessionId to pick its own jsonl (only way to keep them
#            distinct when they share a project_dir).
#
# -----------------------------------------------------------------------------
# STRATEGY — how we classify BUSY / ASKING / IDLE
# -----------------------------------------------------------------------------
# Single authoritative observable: the tail of the JSONL transcript.
#
#   last entry                                | state
#   ------------------------------------------|--------
#   none (fresh session)                      | IDLE
#   `user` (prompt submitted or tool_result)  | BUSY
#   `assistant` with `tool_use` content       | ASKING*
#   `assistant` without `tool_use`            | IDLE
#
#   * Refinement: "ASKING" is ambiguous between (a) permission modal waiting
#     for the user, and (b) tool was approved and is now executing (or
#     already executed — in-process tools like Read/Edit/Grep leave no
#     /proc trace and return almost instantly). We disambiguate in three
#     steps, in order:
#
#       Step 1 (parent transcript): does the tail already contain a
#         `tool_result` whose `tool_use_id` matches one of the `tool_use.id`s
#         in the last assistant entry? If yes, the tool has returned → BUSY.
#         This catches the fast in-process-tool case, which has no
#         subprocess to detect via /proc.
#
#       Step 2 (subagent transcripts): is there a live sidechain jsonl
#         under <project_dir>/<sid>/subagents/ whose last u/a entry is
#         non-terminal (subagent still iterating)? If yes → BUSY. This
#         catches long-running Agent tools whose top-level tool_result
#         hasn't landed yet. Subagents are in-process like other fast
#         in-process tools, but runs can take minutes, so Step 1 alone
#         leaves too large an ASKING window. See assumption I.
#
#       Step 3 (/proc): if no matching tool_result and no active subagent,
#         check child subprocess start times against the turn-boundary
#         timestamp (the PREVIOUS u/a entry's timestamp, not the current
#         tool_use entry's — Claude spawns the subprocess ~hundreds of ms
#         BEFORE the tool_use jsonl write completes, so comparing to the
#         tool_use ts itself misses the child):
#           - any child spawned AFTER the previous u/a entry → BUSY;
#           - no such child → ASKING stays.
#         This uses /proc/<cpid>/stat field 22 (`starttime` in clock ticks
#         since boot) plus /proc/stat `btime` (boot epoch). Persistent
#         helpers (socat from /sandbox, editors from Ctrl-G) predate the
#         previous turn boundary and are correctly ignored.
#
# Turn-end override: Claude Code appends `system/turn_duration` and
# `system/away_summary` entries once a turn has completed. If one of
# these appears in the tail after the last user/assistant entry, the
# turn has ended regardless of whether that last entry was a `user`
# tool_result (which would otherwise look mid-turn) → IDLE.
#
# We do not sample over time — no CPU ticks, no mtime deltas, no grace
# windows. Transitions appear with whatever latency the JSONL and /proc
# themselves exhibit, which is the minimum achievable by a passive monitor.
#
# -----------------------------------------------------------------------------
# ASSUMPTIONS — undocumented Claude Code internals this classifier depends on
# -----------------------------------------------------------------------------
# Claude Code does not publish a stable spec for any of the artifacts below.
# Everything here was reverse-engineered from live installations (v2.1.114 at
# time of writing — see the `version` field on any jsonl entry). Each item
# below is an ASSUMPTION with a pointer to the code site that depends on it
# and a note on how to diagnose and fix breakage if the internal changes.
#
# If sessions stop classifying, start by running:
#     jq -c 'del(.message, .snapshot, .content)' <~/.claude/projects/.../*.jsonl
# to get a fieldset-only view of the current on-disk schema, and compare
# against the assumptions below. Most drifts are one renamed field away.
#
# Summary:
#   A. Filesystem layout — sessions/<pid>.json, cwd-to-project-dir encoding,
#      /clear rotation behavior.
#   B. JSONL top-level entry types — which type values we act on vs. skip
#      (enumerated from scanning every project transcript on the system); ISO
#      8601 timestamp format.
#   C. message.content shape — the user=string|list, assistant=list-of-blocks
#      distinction and how breakage would manifest.
#   D. Slash-command audit records — the four <…> string prefixes we filter;
#      how to recognize a new one.
#   E. Turn-end system subtypes — the two that force IDLE (turn_duration,
#      away_summary) vs. the five observed non-turn-end subtypes that must not be
#      added (local_command, api_error, compact_boundary, scheduled_task_fire,
#      informational).
#   F. Tool execution model — "direct child spawned after tool_use timestamp"
#      and what breaks if Claude switches to an orchestrator model.
#   G. Process identity — the 7-byte comm "claude" check.
#   H. /proc schema — field offsets and the Linux constants we rely on.
#   I. Subagent sidechain transcripts — live per-Agent jsonl under
#      <project_dir>/<sid>/subagents/agent-*.jsonl and the terminal rule.
#
# Details:
#
# A. Filesystem layout
#    A1. Per-pid session file: ~/.claude/sessions/<pid>.json
#        Used in: _load_session_probes, SESSIONS_DIR.
#        Verified shape (v2.1.114):
#            {"pid":int, "sessionId":uuid-str, "cwd":abspath-str,
#             "startedAt":ms-int, "version":str, "kind":"interactive",
#             "entrypoint":"cli"}
#        If the filename pattern or the {pid, cwd, sessionId} triplet moves,
#        rewrite _load_session_probes. The only hard requirement is some way
#        to map live pid → current sessionId → transcript path.
#
#    A2. Transcript path: ~/.claude/projects/<cwd-with-"/"-as-"-">/<sid>.jsonl
#        Used in: _find_active_jsonl, PROJECTS_DIR, `encoded = cwd.replace("/", "-")`.
#        If the encoding changes (e.g. includes a hash, or handles "-" in
#        paths differently), update the `encoded = ...` line. Symptom: probes
#        resolve to None for cwds that contain unusual characters.
#
#    A3. sessionId rotation behavior: `/clear` allocates a new sessionId and
#        starts a fresh jsonl, but does NOT rewrite ~/.claude/sessions/<pid>.json.
#        The hint there therefore goes stale until some unknown next write.
#        Used in: _find_active_jsonl's solo-branch fallback to newest-jsonl.
#        If a future version starts rewriting the sessions file atomically
#        on /clear, the newest-jsonl fallback becomes redundant but harmless.
#        If it starts writing a per-session tombstone file or similar, we
#        could drop the solo/multi branching altogether.
#
# B. JSONL top-level entry types
#    B1. Entry types we ACT on: "user", "assistant", "system".
#        Entry types we IGNORE (skipped by _get_last_entry's outer filter):
#        "attachment", "permission-mode", "file-history-snapshot",
#        "last-prompt", "summary".
#        Used in: _get_last_entry's `if kind not in ("user","assistant"): continue`.
#        If a new type appears that represents "user is being asked for
#        something" or "turn ended", add it to the relevant clause.
#
#    B2. Every entry carries "timestamp" as ISO 8601 with "Z" suffix,
#        e.g. "2026-04-19T21:46:27.752Z".
#        Used in: _parse_timestamp.
#        Python 3.11+ fromisoformat accepts "+00:00" but not "Z" before 3.11,
#        so we normalize. If the format changes to epoch-ms or RFC 2822,
#        update _parse_timestamp.
#
# C. JSONL message.content shape
#    C1. "user".message.content may be:
#          - a STRING (plain text prompt OR a slash-command audit record),
#          - a LIST of content blocks (tool_result with {type:"tool_result", ...}).
#        "assistant".message.content is always a LIST of blocks
#        with block.type in {"text","tool_use","thinking","redacted_thinking"}.
#        Used in: _get_last_entry's has_tool_use scan, _is_internal_user_content.
#        If assistant.content ever becomes a bare string again (Anthropic API
#        style), the `any(isinstance(c,dict)...)` check silently returns False
#        and every tool_use becomes invisible → everything classifies as IDLE
#        or BUSY (never ASKING). Symptom: permission menus never show ASKING.
#
#    C2. Tool-use ↔ tool-result correlation:
#          `assistant` content blocks of type "tool_use" carry {id: str, name, ...}.
#          `user` content blocks of type "tool_result" carry {tool_use_id: str, ...}
#          referencing the id of the tool_use they satisfy.
#        Used in: _collect_tool_use_ids, _has_matching_tool_result, _classify's
#        Step 1 fast-path for "tool already returned → BUSY".
#        This is the only way to detect completion of an IN-PROCESS tool
#        (Read/Edit/Grep/Glob/Write/TodoWrite), which leaves no /proc
#        signal. If the field names change (e.g. "id"→"uuid" on the tool_use
#        side, or "tool_use_id"→"tool_call_id" on the tool_result side),
#        the fast-path silently stops firing and in-process tools revert
#        to the F1 limitation (brief ASKING during execution, then BUSY
#        when the next assistant turn lands). Symptom: a session stays on
#        ASKING indefinitely while Claude is clearly processing a Read/Edit
#        result. Fix: grep a fresh jsonl for the tool_use/tool_result
#        blocks and update the field names in the two helpers above.
#
#    C4. Token accounting — `assistant.message.usage`:
#          Each assistant entry carries a `usage` object with at least:
#            input_tokens                    int   — fresh (uncached) input
#            cache_creation_input_tokens     int   — input written to prompt cache
#            cache_read_input_tokens         int   — input served from cache
#            output_tokens                   int   — generated tokens
#          ("Total input" = sum of the three input categories; summing only
#           `input_tokens` underreports by ~100× on cached sessions.)
#          Also present but not currently used:
#            service_tier / speed            str   — "standard" | "priority"
#            cache_creation.ephemeral_{5m,1h}_input_tokens  int
#            server_tool_use.{web_search,web_fetch}_requests int
#            model                           str   — e.g. "claude-sonnet-4-6"
#        Used in: TokenStats, _compute_token_stats.
#        If the usage field is removed or renamed on an assistant entry,
#        the entry contributes 0 to totals (defensive). Symptom:
#        TokenStats show 0 output despite visible assistant activity.
#        Fix: dump `.message.usage` of a recent assistant entry and realign
#        the four field names in _compute_token_stats.
#
#    C3. Non-chronological file order:
#          Entries are NOT necessarily in timestamp order within the jsonl.
#          Observed on v2.1.114: a tool_result for tool_use id X can appear
#          several file-lines EARLIER than the tool_use that produced X.
#          Claude Code evidently flushes buffered entries in a non-strict
#          order during a multi-step turn.
#        Used in: _has_matching_tool_result scans the WHOLE parsed chunk
#        (not just entries before/after `last_idx`) and matches by
#        tool_use_id, which is order-independent.
#        The reverse-walk for `last_idx` also uses file position, not
#        timestamp — so the "last entry" we classify on is the file-last
#        one, which is what Claude Code most recently wrote to disk (and
#        therefore what the live UI is currently displaying as the tail).
#        If Claude Code switches to strict chronological writes, nothing
#        breaks; the file-order heuristic just happens to coincide with
#        timestamp-order.
#
# D. Slash-command audit records (internal user entries to skip)
#    D1. When the user runs a slash command, Claude Code appends user-type
#        entries whose content is a STRING starting with one of:
#            <command-name>…            (the command invocation itself)
#            <local-command-caveat>…    (boilerplate attached to some commands)
#            <local-command-stdout>…    (stdout of locally-run commands)
#            <local-command-stderr>…    (stderr of same)
#        These are NOT user prompts; treating them as one misclassifies a
#        freshly /clear'd session as BUSY.
#        Used in: _INTERNAL_USER_PREFIXES, _is_internal_user_content.
#        If new audit tags appear (likely for new slash-commands), add the
#        prefix to _INTERNAL_USER_PREFIXES. Symptom: a session sits at BUSY
#        indefinitely after some specific slash-command usage — dump the
#        tail and look for a `<something>…</something>` user entry that
#        we're not skipping.
#
# E. Turn-end system subtypes
#    E1. Claude Code appends one of these system entries when a turn has
#        definitively wrapped up and the process is awaiting the next prompt:
#            {type:"system", subtype:"turn_duration", durationMs, messageCount, …}
#            {type:"system", subtype:"away_summary", content:<summary>, …}
#        Used in: _TURN_END_SUBTYPES, _LastEntry.turn_ended, _classify.
#        Without this override, a tool_result user entry appearing as the tail
#        would keep a completed turn showing as BUSY. Other observed system
#        subtypes (NOT turn-ending, must not be added): "local_command",
#        "api_error", "compact_boundary", "scheduled_task_fire",
#        "informational". If a new turn-end subtype appears, add to the
#        frozenset. Symptom: idle sessions permanently stuck on BUSY
#        immediately after a tool call turn.
#
#    E2. `system/turn_duration.durationMs` is the turn's wall-clock compute
#        time in MILLISECONDS (not ms, not seconds, not microseconds).
#        Summed across all turn_duration entries it yields the session's
#        total "active" / "thinking" time. Used in: TokenStats.active_seconds
#        (divided by 1000), which in turn drives throughput_tokens_per_s.
#        If the unit is renamed (e.g. durationSeconds) or the field moves,
#        active_seconds stays at 0 and throughput reports as None ("—"
#        in the CLI). Symptom: a session with plenty of output shows no
#        t/s value. Fix: inspect a fresh turn_duration entry, update the
#        two references in _compute_token_stats.
#
# F. Tool execution model
#    F1. When Claude runs a tool that requires a subprocess (Bash, and
#        anything delegating to one), it spawns a DIRECT child of the claude
#        PID. The child's start time is usually slightly BEFORE the jsonl
#        write of the corresponding `tool_use` entry completes — observed
#        ~100–200 ms ahead of the entry.timestamp on v2.1.114. We therefore
#        do NOT compare child.start to the current tool_use entry's
#        timestamp (that test rejects the child and stays stuck on ASKING);
#        instead we compare to the PREVIOUS u/a entry's timestamp, which is
#        the true turn boundary and is always well before any current-turn
#        tool spawn.
#        Used in: _child_start_times + _classify's Step 2 refinement,
#        _LastEntry.prev_timestamp, _get_last_entry's two-entry walk.
#        In-process tools (Read, Edit, Grep, Glob, Write, TodoWrite, etc.)
#        do NOT spawn a child, so this /proc-based check alone cannot
#        distinguish "permission pending" from "in-process tool executing".
#        That gap is now closed by the transcript-based fast path at
#        Step 1 of _classify (see assumption C2): once a matching
#        tool_result lands in the jsonl, the classifier reports BUSY
#        regardless of /proc signals. The /proc check here handles the
#        pre-tool_result window of subprocess-based tools (Bash et al.)
#        where the child is already running but no tool_result has been
#        written yet.
#        If Claude Code switches Bash to an in-process library, or starts
#        using an orchestrator process (so claude's direct child becomes a
#        persistent helper instead of the tool itself), the refinement
#        breaks. Symptom: `Bash sleep 30` shows as ASKING throughout, OR
#        every session pins to BUSY (if the orchestrator is long-lived).
#        Fix: walk the process tree recursively, or match the new helper
#        by comm and look one level deeper.
#        If the write-vs-spawn ordering changes so tool children appear
#        AFTER the previous turn boundary by a large margin (e.g. Claude
#        batches writes seconds later), consider a grace window on the
#        threshold or switching back to entry.timestamp - epsilon.
#
# G. Process identity
#    G1. Claude Code's `/proc/<pid>/comm` is literally the 7-byte string
#        "claude". If the binary is ever renamed (e.g. to "claude-code"),
#        _is_process_claude returns False for every PID → no sessions
#        detected. Symptom: empty output. Fix: update the comm check.
#
# H. /proc schema (Linux, stable across kernels but noted for completeness)
#    H1. /proc/<pid>/stat field layout: 3rd field onwards = state, ppid,
#        pgrp, …, 22nd field = starttime (clock ticks since boot).
#        After stripping "pid (comm) " the 22nd becomes fields[19].
#        Used in: _child_start_times, _get_proc_stat_fields.
#    H2. /proc/stat contains a "btime <epoch>" line giving boot time.
#        Used in: _boot_time.
#    H3. SC_CLK_TCK gives ticks-per-second (almost always 100).
#        Used in: _CLK_TCK module constant.
#
# I. Subagent sidechain transcripts
#    I1. When Claude runs an Agent tool, it writes a live sidechain
#        transcript at:
#            ~/.claude/projects/<encoded-cwd>/<session-id>/subagents/agent-<agentId>.jsonl
#        Entries carry {isSidechain: true, sessionId: <parent sid>,
#        agentId: <subagent id>, type/message/timestamp: same shape as
#        parent entries}. The subagent's first entry is a `user` with the
#        initial prompt, timestamp within a few ms of the parent's Agent
#        tool_use entry.
#        Used in: _has_active_subagent, which globs agent-*.jsonl under
#        <project_dir>/<sid>/subagents/ and checks each live file's tail.
#        This is the only intrinsic signal that an in-process Agent is
#        currently running — the parent transcript merely shows an
#        unresolved tool_use for minutes. Without this step the classifier
#        reports ASKING for the whole subagent run (Read/Edit/Grep are
#        sub-second so the assumption F1 ASKING window is invisible, but
#        Agent is not).
#        If Claude Code moves or renames the subagents directory (e.g.
#        "sidechains/", or flattens files alongside the parent jsonl),
#        _has_active_subagent silently returns False. Symptom: multi-minute
#        Agent runs flip to ASKING until every sibling tool_result lands.
#        Fix: update the sub_dir path in _has_active_subagent.
#
#    I2. Subagent transcripts contain NO `system/turn_duration` or
#        `away_summary` entries (unlike parent transcripts). Subagent
#        terminal state therefore cannot use the turn_ended flag. Instead:
#        the subagent is considered done iff its last qualifying u/a entry
#        is an `assistant` message with NO tool_use content blocks — this
#        is the final text answer the subagent returns to the parent.
#        Anything else (user tool_result, or assistant with tool_use) means
#        the subagent is mid-iteration. Symmetric with the top-level
#        assistant-without-tool_use → IDLE rule.
#        If a future version starts emitting a turn-end system marker in
#        subagent jsonls, we can tighten this to also consume that marker,
#        but the current rule is still correct.
#
#    I3. Scoping by mtime: _has_active_subagent compares each file's mtime
#        against the parent's `prev_timestamp` (the current turn boundary)
#        and skips subagents from earlier turns. Every such subagent has
#        long since finished writing, so its mtime is strictly less than
#        any post-turn-boundary write. This is a pure performance filter;
#        the classification signal remains the content of the tail.
#        If Claude Code ever touches old subagent jsonls (e.g. for log
#        rotation or batched flushes), the filter could admit stale files,
#        which is harmless — the terminal-rule content check still decides.
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class _LastEntry:
    kind: str  # "user" or "assistant"
    has_tool_use: bool
    timestamp: float | None  # epoch seconds, None if missing/unparseable
    prev_timestamp: float | None  # ts of the u/a entry BEFORE this one (turn boundary)
    turn_ended: bool  # system/turn_duration or away_summary seen after this entry
    tool_resolved: bool  # a matching tool_result exists for this entry's tool_use(s)


# System subtypes emitted by Claude Code that mean the turn has wrapped up.
# Their presence after the last user/assistant entry forces IDLE.
_TURN_END_SUBTYPES = frozenset({"turn_duration", "away_summary"})

# Slash-command audit markers: Claude Code writes these as type="user"
# entries, but they are *not* user prompts — they are internal records of
# commands like /clear, /compact, etc. Including them in the tail scan
# would misclassify a freshly /clear'd session as BUSY.
_INTERNAL_USER_PREFIXES = (
    "<command-name>",
    "<local-command-caveat>",
    "<local-command-stdout>",
    "<local-command-stderr>",
)


@dataclass
class _SessionProbe:
    pid: int
    cwd: str
    session_id_hint: str | None = None
    jsonl: Path | None = None


def _is_process_claude(pid: int) -> bool:
    try:
        comm = Path(f"/proc/{pid}/comm").read_text().strip()
        if comm != "claude":
            return False
        return os.stat(f"/proc/{pid}").st_uid == os.getuid()
    except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
        return False


def _get_proc_stat_fields(pid_or_tid: str | int) -> list[str] | None:
    try:
        raw = Path(f"/proc/{pid_or_tid}/stat").read_text()
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return None
    rparen = raw.rfind(")")
    if rparen < 0:
        return None
    return raw[rparen + 2 :].split()


def _boot_time() -> float:
    """System boot as epoch seconds, from /proc/stat `btime`."""
    try:
        for line in Path("/proc/stat").read_text().splitlines():
            if line.startswith("btime "):
                return float(line.split()[1])
    except OSError:
        pass
    return 0.0


def _child_start_times(pid: int) -> list[float]:
    """Epoch start times of non-zombie direct children of `pid`."""
    btime = _boot_time()
    if btime == 0.0:
        return []
    try:
        entries = os.listdir("/proc")
    except OSError:
        return []
    starts: list[float] = []
    for entry in entries:
        if not entry.isdigit():
            continue
        fields = _get_proc_stat_fields(entry)
        if fields is None:
            continue
        try:
            state = fields[0]
            ppid = int(fields[1])
            # fields[19] = 22nd stat field (starttime in clock ticks since boot)
            starttime_ticks = int(fields[19])
        except (IndexError, ValueError):
            continue
        if ppid != pid or state == "Z":
            continue
        starts.append(btime + starttime_ticks / _CLK_TCK)
    return starts


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
    """Resolve a probe's live JSONL transcript.

    - solo probe for the cwd → newest jsonl in the project_dir. This is
      robust against /clear-driven sessionId rotation where
      sessions/<pid>.json may not reflect the new id.
    - multiple probes share the cwd → each probe's sessionId hint is the
      only way to distinguish them. We do NOT fall back to newest, which
      would cause all same-cwd probes to collide on the same file.
    """
    encoded = cwd.replace("/", "-")
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


def _parse_timestamp(s: str | None) -> float | None:
    if not isinstance(s, str) or not s:
        return None
    # Claude writes ISO 8601 like "2026-04-19T21:46:27.752Z".
    try:
        normalized = s.replace("Z", "+00:00") if s.endswith("Z") else s
        return datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        return None


def _is_internal_user_content(content) -> bool:
    if not isinstance(content, str):
        return False
    stripped = content.lstrip()
    return any(stripped.startswith(p) for p in _INTERNAL_USER_PREFIXES)


def _is_qualifying_ua(obj: dict) -> bool:
    """True if `obj` is a user/assistant entry the classifier should act on."""
    kind = obj.get("type")
    if kind not in ("user", "assistant"):
        return False
    if kind == "user":
        msg = obj.get("message") or {}
        if _is_internal_user_content(msg.get("content") or []):
            return False
    return True


def _collect_tool_use_ids(content) -> set[str]:
    if not isinstance(content, list):
        return set()
    ids: set[str] = set()
    for c in content:
        if isinstance(c, dict) and c.get("type") == "tool_use":
            tid = c.get("id")
            if isinstance(tid, str):
                ids.add(tid)
    return ids


def _has_matching_tool_result(parsed: list[dict], tool_use_ids: set[str]) -> bool:
    """True if any user entry in `parsed` carries a tool_result for one of `tool_use_ids`."""
    if not tool_use_ids:
        return False
    for obj in parsed:
        if obj.get("type") != "user":
            continue
        msg = obj.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for c in content:
            if (
                isinstance(c, dict)
                and c.get("type") == "tool_result"
                and c.get("tool_use_id") in tool_use_ids
            ):
                return True
    return False


def _get_last_entry(path: Path | None) -> _LastEntry | None:
    if path is None:
        return None
    try:
        size = path.stat().st_size
        with path.open("rb") as f:
            if size > TAIL_BYTES:
                f.seek(-TAIL_BYTES, os.SEEK_END)
                f.readline()  # drop possibly-partial first line
            chunk = f.read()
    except OSError:
        return None
    parsed: list[dict] = []
    for raw in chunk.splitlines():
        if not raw.strip():
            continue
        try:
            parsed.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    if not parsed:
        return None

    # Walk backward to find the "last" qualifying u/a entry. Along the way,
    # flip turn_ended if we see a turn-end system subtype after that entry.
    turn_ended = False
    last_idx: int | None = None
    for i in range(len(parsed) - 1, -1, -1):
        obj = parsed[i]
        if last_idx is None and obj.get("type") == "system" and obj.get("subtype") in _TURN_END_SUBTYPES:
            turn_ended = True
            continue
        if _is_qualifying_ua(obj):
            last_idx = i
            break
    if last_idx is None:
        return None

    last_obj = parsed[last_idx]
    last_content = (last_obj.get("message") or {}).get("content") or []
    has_tool_use = any(
        isinstance(c, dict) and c.get("type") == "tool_use" for c in last_content
    )

    # Previous u/a entry (turn boundary for the child-spawn threshold).
    prev_timestamp: float | None = None
    for j in range(last_idx - 1, -1, -1):
        obj = parsed[j]
        if _is_qualifying_ua(obj):
            prev_timestamp = _parse_timestamp(obj.get("timestamp"))
            break

    # Has any tool_result matching a tool_use in the last entry already been
    # written? If so, the tool was approved+executed and Claude is processing
    # — even for in-process tools that never spawn a subprocess.
    tool_resolved = has_tool_use and _has_matching_tool_result(
        parsed, _collect_tool_use_ids(last_content)
    )

    return _LastEntry(
        kind=last_obj.get("type"),
        has_tool_use=has_tool_use,
        timestamp=_parse_timestamp(last_obj.get("timestamp")),
        prev_timestamp=prev_timestamp,
        turn_ended=turn_ended,
        tool_resolved=tool_resolved,
    )


def _compute_token_stats(path: Path | None) -> TokenStats | None:
    """Tally token usage and active compute time from a full jsonl transcript.

    Reads the entire file (not just the tail): token totals are cumulative
    over the whole session. Works in linear time; a 1 MB transcript is
    sub-millisecond. See assumptions C4 and E2 for the fields we depend on.
    """
    if path is None:
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    output = 0
    input_fresh = 0
    input_create = 0
    input_read = 0
    active_ms = 0
    for raw in data.splitlines():
        if not raw.strip():
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        t = obj.get("type")
        if t == "assistant":
            usage = (obj.get("message") or {}).get("usage")
            if isinstance(usage, dict):
                output += int(usage.get("output_tokens") or 0)
                input_fresh += int(usage.get("input_tokens") or 0)
                input_create += int(usage.get("cache_creation_input_tokens") or 0)
                input_read += int(usage.get("cache_read_input_tokens") or 0)
        elif t == "system" and obj.get("subtype") == "turn_duration":
            d = obj.get("durationMs")
            if isinstance(d, (int, float)):
                active_ms += int(d)
    return TokenStats(
        output=output,
        input_fresh=input_fresh,
        input_cache_create=input_create,
        input_cache_read=input_read,
        active_seconds=active_ms / 1000.0,
    )


def _has_active_subagent(jsonl: Path, threshold: float | None) -> bool:
    """True if any subagent transcript for this session is mid-iteration.

    Terminal rule (per assumption I2): last qualifying u/a entry is
    `assistant` with no tool_use → subagent returned. Anything else (user
    tool_result, or assistant with tool_use) = still iterating → BUSY.

    Scoped by file mtime vs `threshold` (parent's prev turn boundary) to
    skip subagents from earlier turns, which are all terminal by now.
    """
    sub_dir = jsonl.parent / jsonl.stem / "subagents"
    if not sub_dir.is_dir():
        return False
    try:
        candidates = list(sub_dir.glob("agent-*.jsonl"))
    except OSError:
        return False
    for f in candidates:
        try:
            mtime = f.stat().st_mtime
        except OSError:
            continue
        if threshold is not None and mtime < threshold:
            continue
        last = _get_last_entry(f)
        if last is None:
            continue
        if last.kind == "assistant" and not last.has_tool_use:
            continue  # subagent returned its final answer
        return True
    return False


def _classify(
    pid: int, entry: _LastEntry | None, jsonl: Path | None = None
) -> ClaudeState:
    if entry is None:
        return ClaudeState.IDLE
    if entry.turn_ended:
        return ClaudeState.IDLE
    if entry.kind == "user":
        return ClaudeState.BUSY
    # entry.kind == "assistant"
    if not entry.has_tool_use:
        return ClaudeState.IDLE
    # tool_use present: disambiguate "permission pending" vs "tool running".
    # (a) If a tool_result matching this entry's tool_use(s) is already in
    #     the transcript, the tool was approved + executed (possibly an
    #     in-process tool like Read/Edit/Grep that leaves no /proc signal),
    #     and Claude is processing the result → BUSY.
    if entry.tool_resolved:
        return ClaudeState.BUSY
    # (b) A long-running Agent runs in-process so has no /proc child, and
    #     its parent tool_result may not land for minutes (parallel-tool
    #     batches are gated on the slowest sibling). Check sidechain
    #     transcripts for live subagent activity.
    if jsonl is not None and _has_active_subagent(jsonl, entry.prev_timestamp):
        return ClaudeState.BUSY
    # (c) Otherwise check /proc for a subprocess spawned for this turn.
    #     Reference time: the PREVIOUS u/a entry's timestamp, not this one's.
    #     Empirically Claude spawns the subprocess a few hundred ms BEFORE
    #     the tool_use entry's jsonl write, so comparing to entry.timestamp
    #     misses the child. Any child spawned after the previous turn
    #     boundary is a candidate tool-execution child. Falls back to
    #     entry.timestamp when there's only one entry in the scanned tail.
    threshold = entry.prev_timestamp if entry.prev_timestamp is not None else entry.timestamp
    if threshold is not None:
        for start in _child_start_times(pid):
            if start > threshold:
                return ClaudeState.BUSY
    return ClaudeState.ASKING


def _load_session_probes() -> list[_SessionProbe]:
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
        if not (isinstance(pid, int) and isinstance(cwd, str)):
            continue
        if not _is_process_claude(pid):
            continue
        probes.append(
            _SessionProbe(
                pid=pid,
                cwd=cwd,
                session_id_hint=session_id if isinstance(session_id, str) else None,
            )
        )
    return probes


# =============================================================================
# Public API
# =============================================================================


def get_sessions() -> list[ClaudeSession]:
    """Return live Claude sessions for the current user, with state.

    Non-blocking: single /proc + filesystem pass, no sampling window.
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
        entry = _get_last_entry(p.jsonl)
        if p.jsonl is not None:
            sid = p.jsonl.stem
        else:
            sid = p.session_id_hint or ""
        sessions.append(
            ClaudeSession(
                path=p.cwd,
                name=os.path.basename(p.cwd.rstrip("/")),
                id=sid,
                state=_classify(p.pid, entry, p.jsonl),
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


def _humanize_count(n: int) -> str:
    """Short human-readable integer: 12345 → '12.3K', 4_567_890 → '4.6M'."""
    if n < 1000:
        return str(n)
    if n < 1_000_000:
        return f"{n / 1000:.1f}K"
    if n < 1_000_000_000:
        return f"{n / 1_000_000:.1f}M"
    return f"{n / 1_000_000_000:.1f}G"


def main() -> int:
    sessions = get_sessions()
    state_counts = get_state_counts(sessions)

    print(
        " ".join(
            [
                _colorize(f" {n} {state} ", state, n > 0)
                for state, n in state_counts.items()
            ]
        )
    )
    print()
    for s in sessions:
        state_colored = _colorize(f" {s.state:^6} ", s.state)
        sid = s.id.split("-")[-1]
        if s.stats is not None:
            out_s = _humanize_count(s.stats.output)
            in_s = _humanize_count(s.stats.input_total)
            tput = s.stats.throughput_tokens_per_s
            tput_s = f"{tput:.0f} t/s" if tput is not None else "—"
            metrics = f"  out:{out_s:>6}  in:{in_s:>6}  {tput_s:>7}"
        else:
            metrics = ""
        print(f"{sid} {state_colored} {s.name:<28}{metrics}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
