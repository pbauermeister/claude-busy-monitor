# Claude session state detection — design notes

Companion to `claude_busy_monitor.py`. **Read this first** before changing the
classifier or reacting to misclassification reports. Everything documented
here was reverse-engineered from a live Claude Code install (no public
schema); each section names the code site that depends on it and the
diagnostic symptom that appears when the underlying assumption drifts.

## Strategy

Two on-disk sources, both written by Claude Code itself:

1. `~/.claude/sessions/<pid>.json` — `{pid, cwd, sessionId, status, waitingFor, …}`.
   Enumeration source AND authoritative state. See [A1](#a1-per-pid-session-file)
   and [A4](#a4-live-status-claude-code-v21119).
2. `~/.claude/projects/<encoded-cwd>/<sid>.jsonl` — per-session transcript.
   Used only to total token usage. See [A2](#a2-transcript-path) and
   [B](#b-token-usage).

State classification is one table, no inference:

| `probe.status`  | state    | notes                                  |
| --------------- | -------- | -------------------------------------- |
| `"busy"`        | `BUSY`   |                                        |
| `"idle"`        | `IDLE`   |                                        |
| `"waiting"`     | `ASKING` | `waitingFor` says why; we don't branch |
| missing / other | dropped  | requires Claude Code v2.1.119+         |

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
}
```

The hard requirement is mapping live pid → cwd → sessionId → status. If
the filename pattern or that quadruple of fields moves, rewrite
`_load_session_probes`.

### A2. Transcript path

`~/.claude/projects/<cwd-with-"/"-as-"-">/<sid>.jsonl`. Used in
`_find_active_jsonl`, line `encoded = cwd.replace("/", "-")`.

If the encoding changes (hash, different escape rules, handling of `-` in
path segments), update that line.

**Symptom** if it drifts: token stats report `None` for cwds with unusual
characters; state classification is unaffected (it doesn't read the JSONL).

### A3. /clear sessionId rotation

`/clear` allocates a new sessionId and starts a fresh JSONL but does not
necessarily rewrite `~/.claude/sessions/<pid>.json` immediately. The
probe's `sessionId` can therefore lag behind the live id.

Used in `_find_active_jsonl`:

- **Solo probe for the cwd** → fall back to the newest `*.jsonl` in the
  project directory. Robust against the lag.
- **Multiple probes share the cwd** → each uses its own `sessionId` hint;
  do _not_ fall back to newest, which would collide them on the same file.

If a future version starts rewriting the sessions file atomically on
`/clear`, the newest-jsonl fallback becomes redundant but harmless.

### A4. Live status (Claude Code v2.1.119+)

`status` ∈ `{"busy", "idle", "waiting"}`; `waitingFor` (string, present
when status is `"waiting"`) carries the waiting reason. Observed values:

- `approve <ToolName>` — permission modal for a specific tool
  (`approve Bash`, `approve Edit`, …). The exact tool name comes from
  Claude's tool registry.
- `worker request` — pending bridge worker request.
- `sandbox request` — pending sandbox approval.
- `dialog open` — local slash-command JSX dialog (e.g. `/hooks` UI).
- `input needed` — generic fallback when none of the above applies.

Used in `_PROBE_STATUS_MAP` (the three-row table) and the
`isinstance(status, str)` check in `_load_session_probes`.

**Source of truth in the binary:** Claude Code derives the value with

```js
let TY = Cw || tA ? "waiting" : j4 || X_ ? "busy" : "idle";
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

and validates loaded probes against `vM1 = ["busy","idle","waiting"]`.
Both expressions appear in `strings $(which claude)`.

**Symptom** if renamed or removed: every session falls out of the listing
(state map returns `None` for the new field name).

**Fix:** re-grep the binary for `vM1=` and the `gS$({status` call site,
then update `_PROBE_STATUS_MAP` (the three values) and the
`data.get("status")` extraction in `_load_session_probes`.

If Claude Code adds a fourth `status` value, decide whether it maps to
ASKING, BUSY, or a new ClaudeState — _do not_ silently drop it (the loader
treats unknown statuses as "skip the session", which would make new-state
sessions vanish from the listing).

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

`/proc/<pid>/comm` is literally the 7-byte string `"claude"`. Used in
`_is_process_claude` to filter dead pids and non-claude processes (the
sessions directory is per-user but the loader still validates each pid).

**Symptom** if the binary is renamed (e.g. to `claude-code`):
`get_sessions()` returns `[]`. The probe files exist but every pid fails
the comm check.

**Fix:** update the literal in `_is_process_claude`.

This is Linux-only (`/proc`). Porting to macOS/BSD requires replacing
the comm check with `ps -o comm=` or equivalent.

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
strings "$(which claude)" | grep -E '"(busy|idle|waiting)"|vM1=' | head

# 5. Where does claude write the status field?
strings "$(which claude)" | grep -oE '.{40}gS\$\(\{status[^}]+\}' | head
```

Recipes 4 and 5 are the binary-side check for [A4](#a4-live-status-claude-code-v21119).
If the values printed by recipe 4 don't match `_PROBE_STATUS_MAP`, that's
the drift.

## Repair playbook

| Symptom                                         | Likely assumption     | Fix                                                      |
| ----------------------------------------------- | --------------------- | -------------------------------------------------------- |
| `get_sessions()` returns `[]` on a live install | C (or A1 missing)     | Check `comm`, then `ls ~/.claude/sessions/`              |
| All sessions reported BUSY                      | A4 status enum        | Run recipe 4; update `_PROBE_STATUS_MAP`                 |
| One session has `state` but no `stats`          | A2 or A3              | Confirm transcript path encoding; check /clear rotation  |
| Token totals look 100× too low                  | B `input_tokens` only | Reconfirm cache fields are still summed                  |
| Sessions in known-old claude versions vanish    | expected (A4)         | Migrate: `/exit` + `claude --resume <sessionId>`         |
| New `status` value appears, sessions vanish     | A4                    | Add it to `_PROBE_STATUS_MAP` (decide which ClaudeState) |

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
