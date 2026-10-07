# 0023 — Detect backgrounded sessions (parked front-end, bg job process)

- GH issue: #23
- Branch: `impl/0023-detect-backgrounded-sessions`
- Opened: 2026-10-07
- Closed: 2026-10-07

## 1. Mandate

- Author: agent
- Model: Claude Fable 5.1
- Review: pending

### 1.1 Context

Execution, fast-path. Scope source: user bug report — "Project X is reported to be BUSY. But, as far as I can tell, it is waiting for prompt. Please analyze the state of agent(s)." Analysis confirmed the report; user then: "Do all the 2 fixes." Accepted on 2026-10-07.
Predecessor: #21 (shell status) — same README §A4 playbook family.

### 1.2 Problem statement

Claude Code v2.1.289 can move an interactive session to the background (`claude bg-pty-host`). The affected project then had two probe files for one cwd:

1. Front-end (`kind: "interactive"`, `claude -r`, comm `claude`): `status: "busy"`, frozen since the park on 2026-10-05 19:25 UTC, carrying `parkedJobId`; transcript ends with a `continued-in` record.
2. Background job (`kind: "bg"`, versioned binary by full path, comm `2.1.289`): `status: "idle"` since 2026-10-06 16:40 UTC, the real state.

Two loader defects combined: `_is_process_claude` required comm `"claude"` and dropped the bg job; the parked front-end was trusted. Being then solo for the cwd, it took the newest transcript (the bg job's), so the listing showed the bg session id with the front-end's stale BUSY.

### 1.3 Design decisions

- Skip probes whose `parkedJobId` is a string. Mirrors Claude Code's own liveness rule (`if(r.kind==="interactive"&&r.parkedJobId!==void 0)continue;`). `null`/absent means un-parked.
- Accept the versioned-binary launch form by exe path (`…/claude/versions/<ver>`), not by relaxing comm to "anything": a parent-dir test on `/proc/<pid>/exe` is as specific as the old literal.
- No change to the §A3 solo newest-jsonl fallback: the parked front-end touches its transcript hourly, so id/token stats may come from the wrong file after a quiet hour. Recorded as a known gap (README §A3, TODO.md), not fixed here — it is a transcript-selection question, outside the two-fix brief.

### 1.4 Acceptance criteria

1. A probe with string `parkedJobId` does not surface; one with `parkedJobId: null` does.
2. `_is_process_claude` accepts a process whose exe is `…/claude/versions/<ver>` with a non-`claude` comm; still rejects unrelated and dead pids.
3. Backgrounded project on the live install reports IDLE, once.
4. README-STATE-DETECTION.md documents §A5 (backgrounding) and the two launch forms in §C; recipe + playbook rows added.
5. `make test` green; CHANGES.md v1.0.6 entry written.

### 1.5 Coverage check

Within charter scope.

## 2. Execution plan

- Author: agent
- Model: Claude Fable 5.1
- Review: pending

### 2.1 Steps

1. Diagnose: dump both probes, `/proc` comm/exe/cmdline, transcript tails, `strings` the binary for `parkedJobId` setters and the `kind`/`status` validation arrays.
2. `_sessions.py`: skip string `parkedJobId` in `_load_session_probes`; `_is_process_claude` gains the exe-path test (uid check first).
3. Tests: two parked-probe cases in `tests/unit/test_probe_parsing.py`; new `tests/smoke/test_process_identity.py` spawning `sleep` copies as `bin/claude` and `share/claude/versions/2.1.289`; mocked e2e scenario (parked + bg probe, same cwd → one IDLE session).
4. Docs: README-STATE-DETECTION.md (strategy note, §A1 fields, §A3 gap, new §A5, §C rewrite, recipe 6, playbook rows); README.md compatibility line; CHANGES.md v1.0.6.
5. `make format`; `make test` + e2e; live verify; devlog; commit; push; PR `Closes #23`. TODO.md gap entry committed on `main`.

### 2.2 Scope boundary

Probe loader + process identity, their docs/tests. No change to the status map, transcript selection, token stats, or CLI.

## 3. Closure

- Author: agent
- Model: Claude Fable 5.1
- Review: pending

### 3.1 Implementation deviations

None. The §A3 transcript-selection gap was discovered during live verification and recorded rather than fixed (§ 1.3 item 3).

### 3.2 File inventory

- modified: `src/claude_busy_monitor/_sessions.py` — parked-probe skip; two-form `_is_process_claude`; docstring note.
- modified: `tests/unit/test_probe_parsing.py` — `…_drops_parked_front_end_probe`, `…_keeps_probe_when_parked_job_id_is_null`.
- new: `tests/smoke/test_process_identity.py` — four tests over spawned `sleep` copies.
- modified: `tests/e2e/test_classifier_observes_mocked_sessions.py` — `test_classifier_reports_backgrounded_session_from_its_bg_probe`.
- modified: `README-STATE-DETECTION.md` — strategy note; §A1 example fields; §A3 known gap; new §A5; §C rewrite; recipe 6; two playbook rows.
- modified: `README.md` — compatibility line mentions `/proc/<pid>/exe`.
- modified: `CHANGES.md` — v1.0.6 entry.
- new: `architecture/devlog/0023-detect-backgrounded-sessions.md` — this devlog.
- modified on `main`: `TODO.md` — transcript-selection gap.

### 3.3 Verification commands

```bash
for f in ~/.claude/sessions/*.json; do pid=$(jq .pid "$f"); [ -d /proc/$pid ] && \
  echo "$pid $(cat /proc/$pid/comm) $(jq -r '[.kind,.status,(.parkedJobId//"-")]|@tsv' "$f")"; done
strings ~/.local/share/claude/versions/2.1.289 | grep -o '.\{120\}parkedJobId.\{120\}' | head
make test                                   # 32 unit + 18 smoke green
uv run pytest tests/e2e                     # 3 passed, 1 skipped
uv sync --reinstall-package claude-busy-monitor --extra dev   # __version__ → 1.0.6
uv run python -c "from claude_busy_monitor import get_sessions; \
  print([(s.name,str(s.state)) for s in get_sessions()])"     # affected project: idle
```

### 3.4 Coverage check

Within charter scope.

### 3.5 Test review

- _Coverage_: (b) new tests for both changes. Parked-probe skip: two unit tests (string → dropped, `null` → kept). Process identity: smoke test with a real spawned process at `…/claude/versions/2.1.289` (comm asserted `2.1.289`), plus launcher form, unrelated version-like name, dead pid. Mocked e2e covers the combined scenario end-to-end (one IDLE session, bg id). The parked unit test and the versioned-binary smoke test both fail against pre-change code.
- _Effectiveness_: no test bit during the task.

### 3.6 Gate check

- AC #1: ✓ — two unit tests.
- AC #2: ✓ — four smoke tests.
- AC #3: ✓ — live `get_sessions()` shows the affected project once, IDLE (was BUSY).
- AC #4: ✓ — §A5, §C, recipe 6, playbook rows.
- AC #5: ✓ — `make test` green; v1.0.6 in CHANGES.md.

### 3.7 Manual validation

Live install, affected project with both probes present (front-end busy + parked, bg idle). Before: `[('affected', 'busy')]` keyed on the bg session id. After: `[('affected', 'idle')]`. Listed id was the front-end transcript's (newest mtime: parked process touches it hourly) — the recorded §A3 gap.

### 3.8 Retrospective

| #   | Point                                                                                               | Agent    | User |
| --- | --------------------------------------------------------------------------------------------------- | -------- | ---- |
| 1   | Diagnosis from probe files + `/proc` + binary strings took one pass; README recipes were adequate   | well     |      |
| 2   | Two independent defects masked each other (bg drop made the stale probe solo); worth a playbook row | surprise |      |
| 3   | Smoke test spawns real processes instead of mocking `/proc` reads — exercises the kernel path       | well     |      |
| 4   | Transcript-selection gap found only at live verification; deferred, not fixed                       | not well |      |

### 3.9 Verdict

**Recommendation**: Accept with reservations.

**Rationale**:

- All ACs met; both root causes confirmed against the binary and fixed on the live install.
- Regression tests at three levels fail against pre-change code.
- `make test` and e2e green; no public API change.

**Reservations**:

1. §A3 newest-jsonl fallback can pick the parked front-end's transcript (wrong id / token totals, correct state). Captured in TODO.md; needs a decision on hint-first selection vs. the /clear-lag rationale behind the fallback.

## Governance trace

| Source                                            | Clause                | Action  | Note                                                                 |
| ------------------------------------------------- | --------------------- | ------- | -------------------------------------------------------------------- |
| CEREMONIES.md `Fast-path task flow`               | Eligibility check     | applied | user brief "do all the 2 fixes"; mechanical; scope ≤ paragraph       |
| README-STATE-DETECTION.md §A4                     | Repair playbook       | applied | binary re-grepped before touching the loader                         |
| CLAUDE.md `Product intent`                        | Attention synthesis   | applied | bg probe's live status is what signals "needs attention"             |
| CLAUDE.md `No task-related commits on main`       | Branch hygiene        | applied | work on `impl/0023-…`; TODO.md entry on `main` per housekeeping rule |
| CLAUDE.md `YAGNI`                                 | Scope discipline      | applied | exe-path test only; transcript selection untouched                   |
| CLAUDE.md `Naming discipline`                     | Outcome-named         | applied | branch / tests describe WHAT (detect backgrounded sessions)          |
| CLAUDE.md `EN_UK for prose`                       | Spelling              | applied | "favour", "recognise" in prose                                       |
| MEMORY.md `Run make format after every code edit` | Formatter clean       | applied | `make format` + `ruff format tests`                                  |
| CEREMONIES.md `Task closure`                      | Task closure ceremony | applied | this section                                                         |

## Resource consumption

| Phase                | Tokens (approx) | Wall time   |
| -------------------- | --------------- | ----------- |
| Diagnosis            | ~35k            | 10 min      |
| Code + tests + docs  | ~25k            | 15 min      |
| Closure (devlog, PR) | ~15k            | 10 min      |
| **Total**            | **~75k**        | **~35 min** |

| Counter                | Value                                   |
| ---------------------- | --------------------------------------- |
| Pre-commit hook fails  | 0                                       |
| Subagent invocations   | 0                                       |
| `/clear` events        | 0                                       |
| Memory rotation events | 0                                       |
| LOC changed            | see `git diff main...HEAD --stat`       |
| Files changed          | 8 on branch (+ TODO.md on `main`)       |
| Commits on branch      | 1 anticipated (single fast-path commit) |
