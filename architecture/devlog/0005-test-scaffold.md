# 0005 — Test scaffold + e2e fixture

- GH issue: #5
- Branch: `impl/0005-test-scaffold`
- Opened: 2026-04-26
- Closed: 2026-04-26

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.7
- Review: user

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
- Review: user

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
- Review: user

### 3.1 Implementation deviations

- **Real bug caught by seed 6 unit test**: `get_state_counts(sessions=[])` was using `sessions or get_sessions()`, which evaluates to `get_sessions()` because `[]` is falsy — empty input was reading from disk instead of returning zeros. Fixed to `sessions if sessions is not None else get_sessions()`. The test scaffold paid for itself before it was even committed.
- **Real-CC e2e marked `xfail` + `skipif`**: the dummy A/B/C scenario per § 3.X is structurally implemented (pexpect spawn, threaded staggered start, classifier polling, teardown) but the approval-modal keystroke and TUI sync details need one iteration cycle on a live `claude` binary before assertions can be tightened. Gated behind `CLAUDE_E2E_REAL=1` so default `make test-e2e` never burns API tokens. Mock variant (`test_classifier_observes_mocked_sessions.py`) covers seed 11 fully and runs by default.
- **Help-grep regex bump**: `^#* *[ a-zA-Z_-]+:` was missing `0-9`, so `test-e2e` (digits in name) wasn't rendering in `make help`. Pattern bumped to `[a-zA-Z0-9_-]`.
- **`tests/` not yet covered by `lint`/`format`**: ruff currently lints `src/` only. Test files were formatted by hand via `uv run ruff format tests/`. Worth folding `tests/` into the Makefile lint/format scope in a small follow-up.

### 3.2 File inventory

- modified: `pyproject.toml` — adds `[project.optional-dependencies] e2e = ["pexpect"]`.
- modified: `Makefile` — splits `test` into `test-unit`/`test-smoke`/`test-e2e`/`test-full`; aliases `test` → `test-full`; bumps `check` to use `test-full`; widens help-grep to include digits.
- modified: `src/claude_busy_monitor/_sessions.py` — `get_state_counts(sessions=...)` empty-list bug fix.
- renamed: `tests/test_smoke.py` → `tests/smoke/test_public_api.py`.
- new: `tests/unit/test_probe_parsing.py` (seed 1).
- new: `tests/unit/test_active_jsonl_resolution.py` (seeds 2-3).
- new: `tests/unit/test_token_stats.py` (seed 4).
- new: `tests/unit/test_state_map.py` (seed 5).
- new: `tests/unit/test_state_counts.py` (seed 6).
- new: `tests/smoke/test_version_matches_changes.py` (seed 7).
- new: `tests/smoke/test_install_legacy_roundtrip.py` (seed 8).
- new: `tests/smoke/test_cli_exits_zero.py` (seeds 9 + partial 10).
- new: `tests/e2e/conftest.py` — `isolated_home` fixture, helpers.
- new: `tests/e2e/test_classifier_observes_mocked_sessions.py` (seed 11).
- new: `tests/e2e/test_classifier_observes_real_concurrent_sessions.py` — real-CC scaffolding (xfail/skip).

### 3.3 Verification commands

```bash
make test-unit          # 27 unit tests, ~0.07s
make test-smoke         # 6 smoke tests, ~6s (venv-create dominates)
make test-e2e           # 3 e2e (2 mocked pass, 1 real-CC skipped)
make test-full          # = unit + smoke; ~7s
make check              # = lint + test-full
make cycle              # full destructive cycle (calls test → test-full)
CLAUDE_E2E_REAL=1 make test-e2e   # opt-in: spawns real claude, costs API tokens
```

### 3.4 Coverage check

Within charter scope.

### 3.5 Test review

- _Coverage_: every test seed from #3 § 3.7 has at least one landing test. Seeds 1-6 in unit; 7-9 in smoke; 10-11 in e2e (10 covered by smoke `test_cli_emits_summary_line_for_all_three_states` and 11 by mocked e2e). Seed 7 doubles as regression for the `--reinstall` cache bug (#3); seed 8 doubles as regression for the `uninstall-legacy` asymmetry bug (#3).
- _Effectiveness_: seed 6 unit test caught a real bug — `get_state_counts(sessions=[])` returning the live-system state instead of zeros (fixed in same commit, § 3.1).

### 3.6 Gate check

- Acceptance criteria 1-9: criteria 1-3 met (modules per category + coverage). Criterion 4 partially met — e2e covers 10-11 via the mocked variant; the real-CC dummy A/B/C is structurally in place but `xfail`. Criteria 5-8 met. Criterion 9 met (regression coverage for the two #3 bugs).
- All deliverables committed.
- Mandate review gate: § 1 + § 2 user-attested before code.

### 3.7 Retrospective

| #   | Point                                                                                    | Agent    | User |
| --- | ---------------------------------------------------------------------------------------- | -------- | ---- |
| 1   | Test scaffold caught a real production bug in `get_state_counts` on first run            | well     | well |
| 2   | Mocked e2e + real-CC split keeps `make test-e2e` token-free by default                   | well     | well |
| 3   | Real-CC dummy A/B/C shipped as xfail rather than untested speculative code               | well     | well |
| 4   | help-grep `0-9` gap surfaced only when `test-e2e` was added — should've been spotted     | not well | well |
| 5   | Per-target inline `uv sync --extra dev` makes test targets self-bootstrap on a clean box | well     | well |
| 6   | `make test-e2e` opt-in via env var pattern is reusable for future cost-bearing tests     | surprise | well |

### 3.8 Demo scenario (actual)

Mocked variant (always runs):

```bash
make test-e2e
# tests/e2e/test_classifier_observes_mocked_sessions.py ..
# tests/e2e/test_classifier_observes_real_concurrent_sessions.py s
# 2 passed, 1 skipped
```

Real-CC variant (opt-in; spawns three concurrent `claude` processes per § 1's brief):

```bash
CLAUDE_E2E_REAL=1 make test-e2e
# (currently xfail — needs one iteration cycle on a live claude TUI to tighten
# approval-modal keystrokes and prompt-ready synchronization)
```

### 3.9 Forward-looking check

- Test scaffold is the foundation TODO #2 (now graduated to #5) was meant to be — subsequent TODOs (#3 README polish, #4 PyPI publish) now have a regression net underneath them.
- Real-CC e2e iteration is a small, well-scoped follow-up: drive `claude` on a tmpdir HOME, observe approval-modal keystroke (likely `1\r`), tighten the assertions in `test_classifier_observes_real_concurrent_sessions.py`. Probably one short session.
- `tests/` outside `lint`/`format` scope is technical debt — small follow-up.

### 3.10 Verdict

**Recommendation**: Accept with reservations.

**Rationale**:

- 27 unit + 6 smoke + 2 mocked e2e tests green; all #3 § 3.7 seeds have at least one landing test.
- Bug caught and fixed (`get_state_counts(sessions=[])`); regression coverage now in place.
- Makefile interface settled (`test-unit`, `test-smoke`, `test-e2e`, `test-full`, `test` aliases).

**Reservations**:

1. Real-CC dummy A/B/C scenario is xfail / opt-in — needs one iteration cycle on live `claude` to tighten. Tracked via the `xfail` marker; will fall over loudly when fixed.
2. `tests/` not in `lint`/`format` Makefile scope — manual `ruff format tests/` for now. Follow-up.

## Governance trace

| #   | Requirement                  | Source                     | How met                                     |
| --- | ---------------------------- | -------------------------- | ------------------------------------------- |
| 1   | Devlog entry                 | charter § 12.7 / CLAUDE.md | `architecture/devlog/0005-test-scaffold.md` |
| 2   | GH issue with category tag   | CLAUDE.md                  | #5 (`[impl]`)                               |
| 3   | Branch from main             | CLAUDE.md                  | `impl/0005-test-scaffold`                   |
| 4   | Mandate review gate          | CEREMONIES § Task start    | § 1 + § 2 user-attested before code         |
| 5   | Author/Model/Review metadata | charter § 12.1             | per-section blocks present                  |
| 6   | Acceptance criteria          | charter § 12.7             | § 1.7 (9 criteria)                          |
| 7   | Test plan in mandate         | CEREMONIES § Task start    | § 1.6 (this task IS the test plan)          |
| 8   | Coverage check               | charter § 12.5             | § 1.8 + § 3.4                               |
| 9   | Test review at closure       | CEREMONIES § Task closure  | § 3.5                                       |
| 10  | Demo scenario                | CEREMONIES § Task closure  | § 3.8 (mocked variant + real-CC opt-in)     |
| 11  | Retrospective voting table   | CEREMONIES § Task closure  | § 3.7                                       |
| 12  | Forward-looking check        | CEREMONIES § Task closure  | § 3.9                                       |
| 13  | Verdict (self-assessment)    | devlog/CLAUDE.md           | § 3.10                                      |
| 14  | Framework reuse trigger      | CLAUDE.md                  | § 1.5 (pexpect for interactive-CLI driving) |

## Resource consumption

| Metric                   | Value                                                                                |
| ------------------------ | ------------------------------------------------------------------------------------ |
| Wall time                | ~3 h (devlog, scaffold, unit, smoke, Makefile, e2e, closure)                         |
| LOC changed              | +890 / -6 (`git diff main...HEAD --stat`, incl. devlog)                              |
| Files changed            | 15 (excl. devlog): pyproject, Makefile, \_sessions.py, 11 new test modules, 1 rename |
| Commits on branch        | 7 agent + 1 user attestation                                                         |
| Pre-commit hook failures | 0                                                                                    |
| Subagent invocations     | 0                                                                                    |
| `/clear` events          | 0                                                                                    |
| Memory rotation events   | 0                                                                                    |
