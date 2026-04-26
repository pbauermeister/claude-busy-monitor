# 0005 — Test scaffold + e2e fixture

- GH issue: #5
- Branch: `impl/0005-test-scaffold`
- Opened: 2026-04-26
- Closed: _(filled at closure)_

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

### 1.1 Context

Predecessor: #3 (split monolith). Eleven test seeds were enumerated in #3 § 3.7 — this task lands them as actual tests. Two real bugs caught during #3 PR review (`--reinstall` cache, `install-legacy`/`uninstall-legacy` asymmetry) become regression targets.
Source brief: `TODO.md` § 1 (test categories, naming, Makefile interface).
Existing scaffold: `tests/test_smoke.py` (single test asserting public API reachable, added in #3 to unblock `make cycle`).

### 1.2 Task nature

Execution.

### 1.3 Problem statement

Test surface is one smoke test; categories and Makefile interface defined only in TODO prose. Eleven seeds from #3 § 3.7 lack landing places; two known bugs lack regression coverage.

### 1.4 Goal

`tests/{unit,smoke,e2e}/` with at least one module per category; Makefile exposes `test-unit`, `test-smoke`, `test-e2e`, `test-full` (default = unit + smoke; e2e opt-in). e2e demo fixture drives real Claude Code sessions on throwaway projects to exercise the classifier end-to-end.

### 1.5 Design decisions

- **Layout**: `tests/unit/`, `tests/smoke/`, `tests/e2e/`. Existing `tests/test_smoke.py` moves under `tests/smoke/`.
- **Naming**: descriptive, active voice, present tense (e.g. `test_classifier_drops_session_when_status_unknown`). No modal verbs (`should`, `must`, `shall`). Per CLAUDE.md and TODO #1.
- **Unit isolation**: fake probe-file and transcript inputs (no reads from real `~/.claude/`). Parametrize edge cases inline.
- **e2e framework reuse**: drive `claude` via **pexpect** (pseudo-tty automation — well-known solved domain for interactive-CLI scripting). Hand-rolled stdin/PTY harness would re-invent it. Per CLAUDE.md framework-reuse trigger. Add as `[project.optional-dependencies] e2e` (separate extra so the fast unit/smoke loop doesn't pull it).
- **e2e isolation**: per-fixture `HOME=<tmpdir>` override so dummy sessions never touch the user's real `~/.claude/`. Teardown is `rm -rf <tmpdir>` — idempotent.
- **Concurrency model**: dummy A/B/C run as separate `pexpect.spawn` processes; orchestration via threads with staggered start times. asyncio is overkill for three timed branches.
- **Makefile interface**: `test-unit` (uv run pytest tests/unit), `test-smoke` (tests/smoke), `test-e2e` (tests/e2e — opt-in), `test-full` = unit + smoke. Existing `test` aliases `test-full`. `check` umbrella stays = `lint test-full` (does not pull e2e). e2e is run manually or in a dedicated CI job.
- **CI**: not in scope. Wired in a follow-up task once the scaffold settles.

### 1.6 Test plan / fixtures

This task is itself the test scaffold, so verification is meta-level:

1. `make test-unit` runs ≥ 6 unit tests (#3 § 3.7 seeds 1–6) and passes.
2. `make test-smoke` extends the existing public-API smoke + adds CLI-exit-0 + version-consistency + install-legacy round-trip (#3 § 3.7 seeds 7–9 partial).
3. `make test-e2e` runs the dummy A/B/C scenario, completes < 90 s wall, cleans up state.
4. `make test-full` (= unit + smoke) and `make test-e2e` are independent — e2e is not pulled into the fast default.
5. `make check` still passes.

### 1.7 Acceptance criteria

1. `tests/{unit,smoke,e2e}/` directories with ≥ 1 module each.
2. Unit tests cover #3 § 3.7 seeds 1–6 (probe parsing, solo/multi disambiguation, path encoding, token-stats summation, `_PROBE_STATUS_MAP`, `get_state_counts` empty case).
3. Smoke tests cover seeds 7–9 plus the existing public-API smoke.
4. e2e tests cover seeds 10–11 via the dummy A/B/C scenario.
5. Makefile gains `test-unit`, `test-smoke`, `test-e2e`, `test-full`; existing `test` aliases `test-full`.
6. `pyproject.toml` declares the e2e dep (pexpect) under a dedicated `e2e` extra.
7. Test function names follow the active-voice / no-modal-verb convention.
8. `make check` still passes.
9. Regression coverage for two #3 bugs: `--reinstall` rebuild (seed 7) and install-legacy/uninstall-legacy round-trip (seed 8).

### 1.8 Coverage check

Within charter scope.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

### 2.1 Steps

1. `pyproject.toml`: add `[project.optional-dependencies] e2e = ["pexpect"]`.
2. Create `tests/unit/`, `tests/smoke/`, `tests/e2e/` skeletons; move `tests/test_smoke.py` → `tests/smoke/test_public_api.py`.
3. Unit tests covering seeds 1–6 (one module per topic): `test_probe_parsing.py`, `test_active_jsonl_resolution.py`, `test_token_stats.py`, `test_state_counts.py`.
4. Smoke tests for seeds 7–9: `test_cli_exits_zero.py`, `test_version_matches_changes.py`, `test_install_legacy_roundtrip.py`.
5. e2e fixture in `tests/e2e/conftest.py`: pexpect-driven CC sessions; per-fixture tmpdir HOME; teardown helper.
6. e2e scenario in `tests/e2e/test_classifier_observes_concurrent_sessions.py`: dummy A/B/C per § 3.X demo brief.
7. Makefile: split `test` into `test-unit`, `test-smoke`, `test-e2e`, `test-full`; alias `test` → `test-full`; help-text update.
8. Run `make check` and `make test-e2e` to verify locally.
9. Devlog § 3 fill (deviations, file inventory, verification, demo scenario, retrospective, verdict).
10. Commit, push, open PR with `Closes #5`.

### 2.2 Scope boundary

In: scaffold layout, unit + smoke + e2e modules, demo fixture, Makefile test interface.
Out: CI workflow (follow-up); README polish (TODO #2); PyPI publish (TODO #3); GH ticket templates (TODO #4); test seed #3.7 items 10–11 are partially covered (rendering invariants are smoke; tmpdir fixture shape is e2e).

## 3. Closure

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

### 3.X Demo scenario (planned, per user brief at task start)

Captured here at task start for fidelity; the actual implementation lands in `tests/e2e/test_classifier_observes_concurrent_sessions.py` and is exercised by `make test-e2e`.

- **Dummy A**:
  - create a throwaway dummy project; start a Claude Code session inside it; let it sit IDLE for 2 s.
  - prompt CC with a question that elicits an `ASKING` state (e.g. an approval-modal-triggering tool call); wait 2 s; respond to the prompt.
  - prompt CC to wait 10 s (e.g. `Sleep 10 seconds via Bash, then say done`) — exercises `BUSY`.
- **Dummy B**: same as A, started 5 s after A.
- **Dummy C**: same as A, started 10 s after A (5 s after B).
- When all three sessions are back to IDLE, destroy the dummy projects completely (sessions, transcripts, project dirs).

Assertions along the timeline:

1. After A's idle window: classifier reports A=IDLE.
2. While A waits for the question response: A=ASKING; concurrently B may be IDLE then ASKING.
3. While A is sleeping in Bash: A=BUSY; B and C overlap with their own ASKING/BUSY phases.
4. End of run: classifier reports zero live sessions; user's real `~/.claude/` is untouched (HOME override verified).

_(Other § 3 subsections — implementation deviations, file inventory, verification commands, test review, gate check, retrospective, forward-looking, verdict — filled at closure.)_

## Governance trace

_(filled at closure)_

## Resource consumption

_(filled at closure)_
