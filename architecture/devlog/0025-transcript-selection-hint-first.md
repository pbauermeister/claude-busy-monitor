# 0025 — Transcript selection: hint-first

- GH issue: #25
- Branch: `impl/0025-transcript-selection-hint-first`
- Opened: 2026-10-07
- Closed: 2026-10-07

## 1. Mandate

- Author: agent
- Model: Claude Fable 5.1
- Review: pending

### 1.1 Context

Execution, fast-path. Scope source: TODO item 7 — "Backgrounded sessions (#23): solo newest-jsonl fallback (README-STATE-DETECTION.md §A3) may pick the parked front-end transcript (touched hourly) — wrong `id`/token totals, state correct. Decide hint-first selection vs. /clear-lag rationale." Plan: devlog 0023 appendix "Follow-up plan". User: "Proceed with TODO item 7 as a fast-path task." Accepted on 2026-10-07.
Predecessor: #23 (reservation 1).

### 1.2 Problem statement

After #23 only the bg job's probe survives for a backgrounded project, so it is solo for its cwd and `_find_active_jsonl` ignores its `sessionId` hint in favour of the newest transcript by mtime. The parked front-end touches its transcript hourly, so after a quiet hour the listing showed the front-end's id and token totals. Observed live before the fix: id `c1e78da9…` (front-end) for a probe whose `sessionId` is `e7506603…`.

### 1.3 Design decisions

- Hint-first (plan step 2a): use `<sessionId>.jsonl` when it exists; newest-by-mtime only when the hint is absent or not yet materialised. `solo` parameter and `cwd_counts` removed.
- Plan step 1 answered from the binary, not a live `/clear`: on 2.1.289 the probe rewrite with the new sessionId is a session-id-change subscription registered right after session registration (`dd((D,B)=>{… fn({sessionId:D,parkedJobId:void 0,updatedAt:Date.now()},n)`). No lag by construction.
- Residual risk bounded: should a lag reappear, the first status transition after `/clear` rewrites the probe (§A4); until then totals are those of the previous transcript, state unaffected. Recorded in README §A3.
- Step 2b (`kind`-based split) not needed; not implemented.

### 1.4 Acceptance criteria

1. A hinted transcript older than an unrelated newer file is selected.
2. Missing hint / no hint falls back to newest; empty or missing project dir returns `None`.
3. Mocked e2e: parked front-end transcript newer than the bg job's → listed id is the bg job's.
4. Live install: backgrounded project lists the bg job's id and totals.
5. README §A3 rewritten; `make test` green; CHANGES.md v1.0.7.

### 1.5 Coverage check

Within charter scope.

## 2. Execution plan

- Author: agent
- Model: Claude Fable 5.1
- Review: pending

### 2.1 Steps

1. Issue #25, branch; `strings` the binary around the sessionId-change handler; compare live probes' `sessionId` with newest transcript (one mismatch: the parked front-end, as expected).
2. `_sessions.py`: `_find_active_jsonl(cwd, hint)` hint-first; drop `solo` and `cwd_counts` in `get_sessions`.
3. Tests: rewrite `tests/unit/test_active_jsonl_resolution.py` for the new signature + hint-beats-newer case (`os.utime`); extend the #23 mocked e2e scenario with a future-mtime front-end transcript.
4. Docs: README-STATE-DETECTION.md §A3 rewrite (hint-first, history, bounded risk), strategy cross-ref, playbook row; CHANGES.md v1.0.7.
5. `make format`; `make test` + e2e; live verify; devlog; commit; push; PR `Closes #25`. TODO item 7 removed on `main`.

### 2.2 Scope boundary

Transcript selection only. No change to probe loading, process identity, status map, or token arithmetic.

## 3. Closure

- Author: agent
- Model: Claude Fable 5.1
- Review: pending

### 3.1 Implementation deviations

None. Plan step 1 was answered by binary analysis instead of a live `/clear` (see § 1.3); the empirical cross-check was the live-probe comparison in § 2.1 step 1.

### 3.2 File inventory

- modified: `src/claude_busy_monitor/_sessions.py` — hint-first `_find_active_jsonl`; `solo`/`cwd_counts` removed.
- modified: `tests/unit/test_active_jsonl_resolution.py` — rewritten for the new signature; `…_hint_beats_newer_unrelated_transcript`, `…_missing_hint_falls_back_to_newest`, `…_empty_project_dir_returns_none`.
- modified: `tests/e2e/test_classifier_observes_mocked_sessions.py` — #23 scenario now makes the front-end transcript newest.
- modified: `README-STATE-DETECTION.md` — §A3 rewrite; strategy cross-ref; playbook row.
- modified: `CHANGES.md` — v1.0.7 entry.
- new: `architecture/devlog/0025-transcript-selection-hint-first.md` — this devlog.
- modified on `main`: `TODO.md` — item 7 removed.

### 3.3 Verification commands

```bash
strings ~/.local/share/claude/versions/2.1.289 | grep -o '.\{300\}registeredName:K,liveSessionId:V}=H' | head -1   # dd(...) subscription
for f in ~/.claude/sessions/*.json; do pid=$(jq .pid "$f"); [ -d /proc/$pid ] || continue; cwd=$(jq -r .cwd "$f"); \
  sid=$(jq -r .sessionId "$f"); d=~/.claude/projects/$(echo "$cwd" | tr / -); \
  echo "$pid ${sid:0:8} $(ls -t "$d"/*.jsonl | head -1 | xargs basename | cut -c1-8)"; done
make test                                   # 32 unit + 18 smoke green
uv run pytest tests/e2e                     # 3 passed, 1 skipped
uv sync --reinstall-package claude-busy-monitor --extra dev   # __version__ → 1.0.7
uv run python -c "from claude_busy_monitor import get_sessions; \
  print([(s.name,s.id[:8],str(s.state),s.stats) for s in get_sessions()])"   # bg job id + totals
```

### 3.4 Coverage check

Within charter scope.

### 3.5 Test review

- _Coverage_: (b) `…_hint_beats_newer_unrelated_transcript` and the extended mocked e2e both fail against pre-change code (newest-mtime picked the future-dated file). Fallback paths keep coverage via the rewritten `without_hint` / `missing_hint` / `empty_project_dir` tests. Removed: `…_multi_without_hint_returns_none` and `…_multi_skips_missing_hint` (behaviour gone with `solo`).
- _Effectiveness_: no test bit during the task.

### 3.6 Gate check

- AC #1–#2: ✓ — unit tests.
- AC #3: ✓ — mocked e2e.
- AC #4: ✓ — live: `('…', 'e7506603', 'idle', TokenStats(output=2042716, input=503844552))`, previously id `c1e78da9`.
- AC #5: ✓ — §A3 rewritten; `make test` green; v1.0.7.

### 3.7 Manual validation

Live install, backgrounded project with parked front-end (transcript mtime newer by hourly touch) and bg job. Before: id `c1e78da9…`, front-end totals. After: id `e7506603…`, bg job totals; state unchanged (idle).

### 3.8 Retrospective

| #   | Point                                                                                         | Agent | User |
| --- | --------------------------------------------------------------------------------------------- | ----- | ---- |
| 1   | Plan appendix from #23 made this a 10-minute execution; the fork (2a/2b) resolved by one grep | well  |      |
| 2   | `/clear` lag answered from the binary rather than a live TUI test (memory: avoid pexpect e2e) | well  |      |
| 3   | Net code shrank (solo/multi branch removed); fewer failure modes, in the README's own spirit  | well  |      |

### 3.9 Verdict

**Recommendation**: Accept.

**Rationale**:

- All ACs met; the #23 reservation is closed on the live install.
- Regression tests at unit and mocked-e2e level fail against pre-change code.
- Code simplified; `make test` and e2e green; no public API change.

## Governance trace

| Source                                             | Clause                | Action  | Note                                                           |
| -------------------------------------------------- | --------------------- | ------- | -------------------------------------------------------------- |
| CEREMONIES.md `Fast-path task flow`                | Eligibility check     | applied | scope = TODO item 7 + devlog 0023 appendix; mechanical         |
| README-STATE-DETECTION.md § Why this design        | Authoritative signal  | applied | hint = what Claude Code records; mtime demoted to fallback     |
| CLAUDE.md `No task-related commits on main`        | Branch hygiene        | applied | work on `impl/0025-…`; TODO.md on `main` per housekeeping rule |
| CLAUDE.md `YAGNI`                                  | Scope discipline      | applied | step 2b not implemented                                        |
| MEMORY.md `Stage explicit paths, never git add -A` | Staging               | applied | named paths only                                               |
| MEMORY.md `Run make format after every code edit`  | Formatter clean       | applied | `make format` + `ruff format tests`                            |
| CEREMONIES.md `Task closure`                       | Task closure ceremony | applied | this section                                                   |

## Resource consumption

| Phase                 | Tokens (approx) | Wall time   |
| --------------------- | --------------- | ----------- |
| Verification (step 1) | ~10k            | 3 min       |
| Code + tests + docs   | ~15k            | 7 min       |
| Closure (devlog, PR)  | ~10k            | 5 min       |
| **Total**             | **~35k**        | **~15 min** |

| Counter                | Value                             |
| ---------------------- | --------------------------------- |
| Pre-commit hook fails  | 0                                 |
| Subagent invocations   | 0                                 |
| `/clear` events        | 0                                 |
| Memory rotation events | 0                                 |
| LOC changed            | see `git diff main...HEAD --stat` |
| Files changed          | 6 on branch (+ TODO.md on `main`) |
| Commits on branch      | 1                                 |
