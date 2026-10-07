# Claude session state detection — design notes

Companion to `src/claude_busy_monitor/_sessions.py`. **Read this first** before
changing the classifier or reacting to misclassification reports. Everything
documented here was reverse-engineered from a live Claude Code install (no
public schema); each section names the code site that depends on it and the
diagnostic symptom that appears when the underlying assumption drifts.

## Strategy

Two on-disk sources, both written by Claude Code itself:

1. `~/.claude/sessions/<pid>.json` — `{pid, cwd, sessionId, status, waitingFor, …}`.
   Enumeration source AND authoritative state. See [A1](#a1-per-pid-session-file)
   and [A4](#a4-live-status-claude-code-v21119).
2. `~/.claude/projects/<encoded-cwd>/<sid>.jsonl` — per-session transcript.
   Used only to total token usage. See [A2](#a2-transcript-path), [A3](#a3-transcript-selection-hint-first) and
   [B](#b-token-usage).

State classification is one table, no inference:

| `probe.status`  | state    | notes                                           |
| --------------- | -------- | ----------------------------------------------- |
| `"busy"`        | `BUSY`   |                                                 |
| `"idle"`        | `IDLE`   |                                                 |
| `"shell"`       | `BUSY`   | shelled-out / local bash; idle-refinement (§A4) |
| `"waiting"`     | `ASKING` | `waitingFor` says why; we don't branch          |
| missing / other | dropped  | requires Claude Code v2.1.119+                  |

A probe carrying a string `parkedJobId` is dropped regardless of its
`status`: it belongs to the parked front-end of a backgrounded session,
whose `status` is frozen; the background job's own probe (`kind: "bg"`)
is the authoritative one. See [A5](#a5-backgrounded-sessions-claude-code-v21289).

Sessions from older Claude Code versions (no `status` field) are silently
dropped. Migrate them by `/exit` + `claude --resume <sessionId>` — the new
process writes a v2.1.119-format probe file and continues the same JSONL
transcript.

### Deliberately _not_ used

The earlier (pre-v2.1.119) classifier inferred state by walking the JSONL
tail, correlating `tool_use` ↔ `tool_result` ids, scanning subagent
sidechain transcripts, reading `/proc/<cpid>/stat` for child-spawn times,
and tracking `system/turn_duration` markers. All of that was a stack of
proxies for what `status` now reports directly. **Do not reintroduce any of
it** unless `status` itself goes away — the proxies layered failure modes
(persistent helpers pinning BUSY, /clear desyncing the transcript, batched
JSONL writes shifting timestamps) that the intrinsic signal eliminates.

## Assumptions (with code sites and repair playbook)

When sessions stop classifying or are wrongly labeled, run the diagnostic
recipes at the bottom and compare against the assumptions below. Most
drifts are one renamed field away.

### A1. Per-pid session file

Path: `~/.claude/sessions/<pid>.json`. Used in `_load_session_probes`.

Required fields (v2.1.119, observed):

```jsonc
{
  "pid": 4116834,
  "sessionId": "e508dfcd-efef-48c7-b9de-a0e233458c35",
  "cwd": "/home/user/projects/claude-busy-monitor",
  "startedAt": 1777170615032,
  "procStart": "133782286",
  "version": "2.1.119",
  "peerProtocol": 1,
  "kind": "interactive",
  "entrypoint": "cli",
  "status": "waiting",
  "waitingFor": "approve Bash",
  "updatedAt": 1777176263534,
  "statusUpdatedAt": 1777176263534, // v2.1.289: when `status` last changed
  "parkedJobId": "e7506603", // v2.1.289: present only on a parked front-end (§A5)
}
```

The hard requirement is mapping live pid → cwd → sessionId → status. If
the filename pattern or that quadruple of fields moves, rewrite
`_load_session_probes`. `kind` ∈ `{"interactive","bg","daemon","daemon-worker"}`
(binary validation array); only `interactive` and `bg` are seen in practice.

### A2. Transcript path

`~/.claude/projects/<cwd-with-"/"-as-"-">/<sid>.jsonl`. Used in
`_find_active_jsonl`, line `encoded = cwd.replace("/", "-")`.

If the encoding changes (hash, different escape rules, handling of `-` in
path segments), update that line.

**Symptom** if it drifts: token stats report `None` for cwds with unusual
characters; state classification is unaffected (it doesn't read the JSONL).

### A3. Transcript selection (hint-first)

`_find_active_jsonl` resolves a probe's transcript as
`<project-dir>/<probe.sessionId>.jsonl` when that file exists, and only
otherwise falls back to the newest `*.jsonl` by mtime (fresh session
whose transcript is not written yet, or a probe without `sessionId`).

History: before #25 a probe that was solo for its cwd always took the
newest file, to cover a `/clear` whose new sessionId had not yet reached
the probe. On v2.1.289 the probe rewrite is a session-id-change
subscription registered right after the session registers
(`dd((D,B)=>{… fn({sessionId:D,parkedJobId:void 0,updatedAt:Date.now()},n)`
in the binary), so the lag no longer exists; and newest-mtime picked the
wrong file for backgrounded sessions, whose parked front-end touches its
own transcript hourly (§A5).

Should the lag reappear, the cost is bounded: `status` is persisted on
every transition (§A4), so at the latest the first turn after `/clear`
rewrites the probe with the current sessionId. Until then the token
totals are those of the previous transcript; state is unaffected.

### A4. Live status (Claude Code v2.1.119+)

`status` ∈ `{"busy", "shell", "idle", "waiting"}`; `waitingFor` (string,
present when status is `"waiting"`) carries the waiting reason.

`"shell"` was added after v2.1.119 (observed on v2.1.175). It is an
_idle refinement_: the binary computes it only when the base status would
be `"idle"` and a shell sub-mode is active (shelled-out / local-bash
context — cf. `local_bash:"shell"`, `CLAUDE_BG_SOURCE??"shell"`):

```js
Y1 = ... ? "waiting" : ... ? "busy" : "idle"; // base status
XA = Y1 === "idle" && Hf ? "shell" : Y1; // persisted status
```

We map `"shell" → BUSY` (not IDLE): although Claude is not running an LLM
turn, the session looks active to the user — something is going on. A
shelled-out session that we labelled idle would read as "free to use".

`waitingFor` observed values:

- `approve <ToolName>` — permission modal for a specific tool
  (`approve Bash`, `approve Edit`, …). The exact tool name comes from
  Claude's tool registry.
- `worker request` — pending bridge worker request.
- `sandbox request` — pending sandbox approval.
- `dialog open` — local slash-command JSX dialog (e.g. `/hooks` UI).
- `input needed` — generic fallback when none of the above applies.

Used in `_PROBE_STATUS_MAP` (the four-row table) and the
`isinstance(status, str)` check in `_load_session_probes`.

**Source of truth in the binary:** Claude Code derives the value with

```js
let TY = Cw || tA ? "waiting" : j4 || X_ ? "busy" : "idle";
TY = TY === "idle" && Hf ? "shell" : TY; // shell refinement (post-v2.1.119)
let If =
  TY !== "waiting"
    ? void 0
    : dK.length > 0
      ? `approve ${dK[0].tool.name}`
      : r
        ? "worker request"
        : a
          ? "sandbox request"
          : tA
            ? "dialog open"
            : "input needed";
gS$({ status: ML, waitingFor: If }); // persisted on every transition
```

and validates loaded probes against the status array, now
`t3f = ["busy","shell","idle","waiting"]` (was `vM1 = [...]` pre-shell).
Both expressions appear in `strings $(which claude)`.

**Symptom** if renamed or removed: every session falls out of the listing
(state map returns `None` for the new field name).

**Fix:** re-grep the binary for the status array (`t3f=` / `vM1=`) and the
`gS$({status` call site, then update `_PROBE_STATUS_MAP` and the
`data.get("status")` extraction in `_load_session_probes`.

If Claude Code adds a _further_ `status` value, decide whether it maps to
ASKING, BUSY, IDLE, or a new ClaudeState — _do not_ silently drop it (the
loader treats unknown statuses as "skip the session", which would make
new-state sessions vanish from the listing). `"shell"` was the first such
addition after v2.1.119; it is mapped to BUSY.

### A5. Backgrounded sessions (Claude Code v2.1.289)

An interactive session can be moved to the background. Claude Code then:

1. Spawns `claude bg-pty-host … -- <versioned-binary> --session-id <new>
--fork-session --resume <old transcript>`: a new process with its own
   probe file, `kind: "bg"`, `jobId: <id>`, and a live `status`.
2. Marks the front-end's probe with `parkedJobId: <same id>` and stops
   updating its `status`: it stays frozen at the last value before the
   park, typically `busy` since parking happens mid-turn.
3. Appends a `continued-in` record to the front-end's transcript.

Used in `_load_session_probes`: a probe whose `parkedJobId` is a string
is skipped. Claude Code applies the same rule in its own liveness logic:

```js
if (r.kind === "interactive" && r.parkedJobId !== void 0) continue;
```

Un-parking rewrites the probe with `parkedJobId: undefined` (setter
`Vkn`), so a `null`/absent field means "not parked".

**Symptom** if the field is renamed: a backgrounded project shows one
session stuck BUSY (the frozen front-end) even when the background job
is idle — the original #23 report.

**Fix:** re-grep the binary for the `parkedJobId` setters (`_8r`/`Vkn`)
and realign the field name in `_load_session_probes`.

### B. Token usage

`assistant.message.usage` in the JSONL carries:

| field                         | meaning                                |
| ----------------------------- | -------------------------------------- |
| `input_tokens`                | fresh (uncached) input                 |
| `cache_creation_input_tokens` | input written to prompt cache          |
| `cache_read_input_tokens`     | input served from cache (~10× cheaper) |
| `output_tokens`               | generated tokens                       |

`TokenStats.input` is the sum of all three input categories — using only
`input_tokens` underreports by ~100× on cache-heavy sessions. Used in
`_compute_token_stats`.

Other fields present on `usage` but not currently summed:
`service_tier`/`speed`, `cache_creation.ephemeral_{5m,1h}_input_tokens`,
`server_tool_use.{web_search,web_fetch}_requests`, `model`.

**Symptom** if a field is renamed/removed: totals silently come back as 0;
the column shows `0` despite visible activity.

**Fix:** dump `.message.usage` of a recent assistant entry
(`jq '.message.usage' <transcript>.jsonl | head`) and realign the four
field names.

If the cache-vs-fresh distinction ever needs to drive cost reporting,
split `TokenStats.input` back into the three categories — the data is
all there, the rollup is just a UX choice.

### C. Process identity

Used in `_is_process_claude` to filter dead pids and non-claude processes
(the sessions directory is per-user but the loader still validates each
pid). Two launch forms are accepted:

| launch form                              | `/proc/<pid>/comm`      | `/proc/<pid>/exe`                      |
| ---------------------------------------- | ----------------------- | -------------------------------------- |
| `claude` launcher (interactive sessions) | `claude`                | `~/.local/share/claude/versions/<ver>` |
| versioned binary by full path (bg jobs)  | `<ver>`, e.g. `2.1.289` | same                                   |

Rule: comm `"claude"`, or exe whose parent directories end in
`claude/versions/`. Before #23 only the comm check existed, so every
background job (§A5) was dropped.

**Symptom** if the binary is renamed (e.g. to `claude-code`) or the
install layout moves: `get_sessions()` returns `[]`, or background jobs
vanish. The probe files exist but every pid fails the identity check.

**Fix:** realign the literal / path test in `_is_process_claude`
(recipe 6 prints what the kernel reports).

This is Linux-only (`/proc`). Porting to macOS/BSD requires replacing
the comm/exe checks with `ps -o comm=` or equivalent.

## Diagnostic recipes

When something looks wrong, run these in order:

```bash
# 1. What does Claude Code itself say about each live session?
jq . ~/.claude/sessions/*.json

# 2. Is the version field above v2.1.119 on every probe?
jq -r '.version + "\t" + (.status // "(no status)") + "\t" + .cwd' \
  ~/.claude/sessions/*.json

# 3. What does the transcript look like for a specific session?
jq -c 'del(.message,.snapshot,.content)' \
  ~/.claude/projects/<encoded-cwd>/<sid>.jsonl | tail -20

# 4. What status values does the current claude binary know about?
strings "$(which claude)" | grep -E '"(busy|shell|idle|waiting)"|t3f=|vM1=' | head

# 5. Where does claude write the status field?
strings "$(which claude)" | grep -oE '.{40}gS\$\(\{status[^}]+\}' | head

# 6. Process identity + background bookkeeping per probe (§A5, §C)
for f in ~/.claude/sessions/*.json; do
  pid=$(jq .pid "$f"); [ -d /proc/$pid ] || continue
  echo "$pid $(cat /proc/$pid/comm) $(readlink /proc/$pid/exe)" \
       "$(jq -r '[.kind, .status, (.parkedJobId // "-"), (.jobId // "-")] | @tsv' "$f")"
done
```

Recipes 4 and 5 are the binary-side check for [A4](#a4-live-status-claude-code-v21119).
If the values printed by recipe 4 don't match `_PROBE_STATUS_MAP`, that's
the drift.

## Repair playbook

| Symptom                                         | Likely assumption     | Fix                                                           |
| ----------------------------------------------- | --------------------- | ------------------------------------------------------------- |
| `get_sessions()` returns `[]` on a live install | C (or A1 missing)     | Check `comm`, then `ls ~/.claude/sessions/`                   |
| All sessions reported BUSY                      | A4 status enum        | Run recipe 4; update `_PROBE_STATUS_MAP`                      |
| One session has `state` but no `stats`          | A2 or A3              | Confirm transcript path encoding; `<sessionId>.jsonl` exists? |
| Token totals look 100× too low                  | B `input_tokens` only | Reconfirm cache fields are still summed                       |
| Sessions in known-old claude versions vanish    | expected (A4)         | Migrate: `/exit` + `claude --resume <sessionId>`              |
| New `status` value appears, sessions vanish     | A4                    | Add it to `_PROBE_STATUS_MAP` (decide which ClaudeState)      |
| Backgrounded project stuck BUSY while idle      | A5                    | Recipe 6: front-end probe has `parkedJobId`; realign skip     |
| Background job (`kind: "bg"`) missing from list | C                     | Recipe 6: comm is a version string; realign exe path test     |

## Why this design

Earlier iterations stacked four proxy signals (file mtime delta,
recent-write grace window, child-process state, CPU ticks) plus a
JSONL-tail inspection to _infer_ state. Each proxy had its own failure
mode and the layering compounded them. Once Claude Code started
publishing `status` directly, every proxy became redundant — the
classifier shrank from ~975 lines to ~280 with strictly fewer failure
modes. The principle, worth preserving when this code is touched:
**read what the system itself records before synthesizing from
proxies.** If a future Claude Code change removes `status`, the right
response is _not_ to re-implement the proxy stack — it's to find the new
authoritative signal first.
