# 0021 — Detect sessions with new "shell" probe status

- GH issue: #21
- Branch: `impl/0021-detect-shell-status`
- Opened: 2026-06-14
- Closed: 2026-06-14

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 1.1 Context

Execution, fast-path. Scope source: user bug report — "claude-busy-monitor detects 1 session but there is another one (pikett-ai-mvp) it misses", later clarified "it was undetected also before I suspended it" (rules out the Ctrl-Z stopped-process state as cause). Accepted on 2026-06-14.

### 1.2 Problem statement

Claude Code (observed v2.1.175) added a fourth probe `status` value, `"shell"` — binary validation array is now `t3f=["busy","shell","idle","waiting"]`. `_PROBE_STATUS_MAP` knew only `busy`/`idle`/`waiting`, so `_load_session_probes` (`_sessions.py:195-197`) treated `"shell"` as unknown and dropped the session. Live repro: `pikett-ai-mvp` (`status:"shell"`) was invisible while running and after Ctrl-Z. Exactly the failure mode README §A4 warned about.

### 1.3 Design decisions

- Map `"shell" → ClaudeState.BUSY` (user decision). The binary derives `"shell"` as an idle refinement (`XA = Y1==="idle" && Hf ? "shell" : Y1`), but to the user a shelled-out session looks active — something is going on — so BUSY, not IDLE. An idle label would read as "free to use".
- No new `ClaudeState`. A `SHELL` member would ripple into badge colours, the counts API, and tests for no decision-relevant gain (YAGNI).

### 1.4 Acceptance criteria

1. A probe with `status:"shell"` surfaces as a BUSY session (not dropped).
2. Existing `busy`/`idle`/`waiting` mappings unchanged.
3. README-STATE-DETECTION.md §A4 + state table document the fourth value.
4. `make test` green; CHANGES.md v1.0.5 entry written.

### 1.5 Coverage check

Within charter scope.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 2.1 Steps

1. Confirm cause against binary (`strings $(which claude)`) and live probe files.
2. Add `"shell": ClaudeState.BUSY` to `_PROBE_STATUS_MAP` (`_sessions.py`).
3. Update README-STATE-DETECTION.md: state table, §A4 (new value + derivation + mapping rationale), source-of-truth array (`vM1`→`t3f`), diagnostic recipe 4.
4. Update tests: `test_state_map.py` (four keys + shell→BUSY); add `test_probe_parsing_accepts_shell_status_as_busy`.
5. CHANGES.md v1.0.5; `make format`; `make test` + e2e; live verify; commit; push; PR `Closes #21`.

### 2.2 Scope boundary

Status-map + its docs/tests only. No change to enumeration, transcript reading, token stats, or process-identity checks.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.8
- Review: pending

### 3.1 Implementation deviations

None. Plan executed as written.

### 3.2 File inventory

- modified: `src/claude_busy_monitor/_sessions.py` — `"shell": ClaudeState.BUSY` + WHY comment.
- modified: `README-STATE-DETECTION.md` — state table row; §A4 rewrite; source-of-truth array + shell ternary; recipe 4; repair-playbook wording.
- modified: `README.md` — §6 corrected: raw `status` set now includes `shell`; "one-row table" → many-to-one synthesis (`shell → busy`). Accuracy fallout from this task's mapping change.
- modified: `tests/unit/test_state_map.py` — four-key assertion; shell→BUSY test.
- modified: `tests/unit/test_probe_parsing.py` — `test_probe_parsing_accepts_shell_status_as_busy`.
- modified: `CHANGES.md` — v1.0.5 entry.
- new: `architecture/devlog/0021-detect-shell-status.md` — this devlog.

### 3.3 Verification commands

```bash
strings "$(which claude)" | grep -oE '\["busy","shell","idle","waiting"\]|t3f='   # confirm enum
make test                                          # 30 unit + 14 smoke green
uv run pytest tests/e2e                             # 2 passed, 1 skipped
uv sync --reinstall-package claude-busy-monitor --extra dev   # refresh __version__ → 1.0.5
uv run python -c "from claude_busy_monitor import get_sessions; \
  print([(s.name,str(s.state)) for s in get_sessions()])"     # pikett-ai-mvp now BUSY
```

### 3.4 Coverage check

Within charter scope.

### 3.5 Test review

- _Coverage_: (b) two new tests. `test_state_map_shell_string_maps_to_BUSY_state` + four-key set assertion lock the map; `test_probe_parsing_accepts_shell_status_as_busy` exercises the full loader path. Both fail against pre-change code (which dropped `"shell"`), so they would have caught the original bug.
- _Effectiveness_: `test_version_matches_changes` bit once during closure (CHANGES.md bump vs stale editable wheel) — resolved with `--reinstall-package`, the known #17 factoring candidate (hit count now 2).

### 3.6 Gate check

- AC #1: ✓ — `test_probe_parsing_accepts_shell_status_as_busy`; live `get_sessions()` shows `pikett-ai-mvp` BUSY.
- AC #2: ✓ — busy/idle/waiting rows unchanged; existing tests green.
- AC #3: ✓ — README state table + §A4 updated.
- AC #4: ✓ — `make test` green (30 unit + 14 smoke); v1.0.5 in CHANGES.md.

### 3.7 Manual validation

Live install, two real sessions present (`586654.json` busy, `1349668.json` shell). Before fix: `get_sessions()` returned only `claude-busy-monitor`. After: both returned, counts `{busy: 2, asking: 0, idle: 0}`.

### 3.8 Retrospective

| #   | Point                                                                                          | Agent | User |
| --- | ---------------------------------------------------------------------------------------------- | ----- | ---- |
| 1   | README §A4 had pre-written the exact playbook for "new status value" — diagnosis was fast      | well  |      |
| 2   | User overruled the IDLE proposal with a clear user-facing rationale (appears active → BUSY)    | well  |      |
| 3   | `test_version_matches_changes` editable-wheel drift recurred (#17 factoring candidate, hit 2)  | not well |   |

### 3.9 Verdict

**Recommendation**: Accept.

**Rationale**:

- All ACs met; root cause confirmed against the binary and reproduced/fixed on the live install.
- Two new regression tests fail against pre-change code.
- `make test` green (30 unit + 14 smoke); e2e green. Single-key map change, no API surface change.

## Governance trace

| Source                                            | Clause                | Action  | Note                                                                    |
| ------------------------------------------------- | --------------------- | ------- | ----------------------------------------------------------------------- |
| CEREMONIES.md `Fast-path task flow`               | Eligibility check     | applied | mechanical; mapping decision made by user upfront; scope ≤ paragraph    |
| README-STATE-DETECTION.md §A4                      | New-status playbook   | applied | "do not silently drop"; decide mapping — followed verbatim              |
| CLAUDE.md `No task-related commits on main`        | Branch hygiene        | applied | all work on `impl/0021-detect-shell-status`                             |
| CLAUDE.md `Naming discipline`                      | Outcome-named         | applied | branch / devlog describe WHAT (detect shell status)                     |
| CLAUDE.md `EN_UK for prose`                        | Spelling              | applied | "recognise", "colour" etc. in prose                                    |
| CLAUDE.md `YAGNI`                                  | Scope discipline      | applied | no new ClaudeState; status-map only                                     |
| MEMORY.md `Run make format after every code edit`  | Formatter clean       | applied | `make format` + `ruff format tests` run before commit                  |
| CEREMONIES.md `Task closure`                       | Task closure ceremony | applied | this section                                                            |

## Resource consumption

| Phase                       | Tokens (approx) | Wall time   |
| --------------------------- | --------------- | ----------- |
| Diagnosis (subagent + grep) | ~30k            | 15 min      |
| Code + docs + tests         | ~20k            | 15 min      |
| Closure (devlog)            | ~20k            | 15 min      |
| **Total**                   | **~70k**        | **~45 min** |

| Counter                | Value                                                          |
| ---------------------- | ------------------------------------------------------------- |
| Pre-commit hook fails  | 0                                                             |
| Subagent invocations   | 1 (Explore — detection-logic search)                         |
| `/clear` events        | 0                                                             |
| Memory rotation events | 0                                                             |
| LOC changed            | see `git diff main...HEAD --stat`                            |
| Files changed          | 7 (`_sessions.py`, README-STATE-DETECTION.md, README.md, 2 tests, CHANGES.md, devlog) |
| Commits on branch      | 1 anticipated (single fast-path commit)                      |
