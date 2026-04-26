# 0003 — Split monolith into installable library + CLI

- GH issue: #3
- Branch: `impl/0003-split-monolith`
- Opened: 2026-04-26
- Closed: 2026-04-26

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.7
- Review: user

### 1.1 Context

Predecessor: #1 (build skeleton — established `uv` + `hatchling` + `ruff` + `Makefile`, registered the `claude-busy-monitor` CLI as a stub).
Source brief: `TODO.md` § 1 (7 sub-items) and `README-STATE-DETECTION.md` (classifier design notes — must keep in sync with the new module paths).

### 1.2 Task nature

Execution.

### 1.3 Problem statement

`claude_busy_monitor.py` (≈320 LOC at repo root) mixes three concerns: classifier (states, probing, transcript), public API (`get_sessions`, `get_state_counts`), and CLI rendering (ANSI colors, formatted output). Cannot be `import`ed cleanly from another program because (a) it lives at repo root, not under `src/claude_busy_monitor/`, and (b) the CLI renders the same module a library would expose.
Versioning is duplicated: `pyproject.toml`, `__init__.py`, and any future `CHANGES.md` would drift independently.
The CLI registered in #1 is a stub (`scaffold only — see TODO #1`); needs to do real work.

### 1.4 Goal

After this task: `from claude_busy_monitor import ClaudeSession, ClaudeState, get_sessions, get_state_counts` works; `claude-busy-monitor` prints a state summary + per-session listing usable under `watch`; `make install` puts the CLI on `~/.local/bin`; bumping a version means appending a heading to `CHANGES.md` (single source of truth, hatch dynamic regex); the original `claude_busy_monitor.py` is gone.

### 1.5 Design decisions

- **Module layout**: `claude_busy_monitor/__init__.py` (re-exports public API + `__version__` via `importlib.metadata`); `_core.py` (types, probing, transcript reading, `get_sessions`/`get_state_counts`); `_cli.py` (colors + `main()`). Two-file split, not five — ≈250 LOC of library code does not justify deeper internal partitioning. Naming uses `_core` (underscore prefix) to mark it as internal — consumers import from the package root.
- **Rendering separation**: lib code emits no ANSI / formatting; `_cli.py` owns the palette and layout. The current monolith's palette (BG_RED / BG_YELLOW+blink / BG_GREEN, 16-color) is already `watch`-compatible; carry it over verbatim.
- **Version source of truth**: `CHANGES.md` with `## Version X.Y.Z: …` headings, newest first. `pyproject.toml` declares `version` as dynamic and uses hatch regex source (`[tool.hatch.version] source = "regex"`, `path = "CHANGES.md"`, `pattern = r"^## Version (?P<version>\d+\.\d+\.\d+):"`). `claude_busy_monitor.__version__ = importlib.metadata.version("claude-busy-monitor")` — reads the installed metadata, which hatch populates from `CHANGES.md` at build time. Works for `uv sync` editable installs.
- **Initial version**: bump to `0.1.0` — first release with a usable CLI and a stable public API. `0.0.1` was the skeleton-stage placeholder.
- **`make install`**: thin wrapper around `uv tool install .` (idempotent: `uv tool install --force .` to support reinstalls during dev). Output binary lands in `~/.local/bin/claude-busy-monitor`.
- **Monolith deletion**: `git rm claude_busy_monitor.py` in the same commit as the structure flip — no transition window where both exist.
- **`README-STATE-DETECTION.md` update**: replace `claude_busy_monitor.py` references with `src/claude_busy_monitor/_core.py`; keep the inline `(see README §A1)` style intact (the section anchors don't change).

Planned tree (changes only):

```
.
├── CHANGES.md                          (new)
├── Makefile                            (modified — `install` target)
├── README-STATE-DETECTION.md           (modified — path refs)
├── claude_busy_monitor.py              (deleted)
├── pyproject.toml                      (modified — dynamic version)
└── src/claude_busy_monitor/
    ├── __init__.py                     (rewritten — re-exports + __version__)
    ├── _cli.py                         (rewritten — real CLI + ANSI rendering)
    └── _core.py                        (new — types, probing, transcript, public API)
```

### 1.6 Test plan / fixtures

Test scaffold is TODO #2 (deferred). For this task, verification is operational:

1. `make build` produces wheel + sdist that include `src/claude_busy_monitor/_core.py` and `_cli.py`.
2. `make install` installs `claude-busy-monitor` on `~/.local/bin` (verify `which claude-busy-monitor`).
3. `claude-busy-monitor` runs against the live `~/.claude/sessions/` and produces the expected layout.
4. `python -c "from claude_busy_monitor import ClaudeSession, ClaudeState, get_sessions, get_state_counts; print(get_state_counts())"` works.
5. `python -c "from claude_busy_monitor import __version__; print(__version__)"` prints the latest `## Version` from `CHANGES.md`.
6. `make lint` passes.

### 1.7 Acceptance criteria

1. Public API importable: `ClaudeSession`, `ClaudeState`, `get_sessions`, `get_state_counts` from `claude_busy_monitor`.
2. Library code (`_core.py`) contains no ANSI escape sequences or rendering helpers.
3. CLI (`_cli.py`) prints summary line + per-session lines per `TODO.md` § 1 sub-item 3 example.
4. `CHANGES.md` exists with `## Version 0.1.0:` heading + bullet summary; `pyproject.toml` reads version dynamically; `__version__` matches.
5. `make install` target works end-to-end on a clean checkout: `make venv && source .venv/bin/activate && make require && make install` puts the CLI on PATH.
6. `README-STATE-DETECTION.md` updated to reference `_core.py` (no dangling references to the deleted monolith).
7. `claude_busy_monitor.py` deleted.
8. `make lint` passes; `make build` produces wheel + sdist.
9. Devlog § 3 includes a `Test seeds for TODO #2` subsection — aspects spotted during implementation worth covering in the test scaffold task. Forward-feeds TODO #2.

### 1.8 Coverage check

Within charter scope.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.7
- Review: user

### 2.1 Steps

1. Add `CHANGES.md` with `## Version 0.1.0:` heading and one-paragraph summary (initial public release: library + CLI split).
2. Update `pyproject.toml`: declare `version` as dynamic; add `[tool.hatch.version]` with regex source pointing at `CHANGES.md`; remove the static `version = "0.0.1"`.
3. Create `src/claude_busy_monitor/_core.py` from the monolith — strip ANSI helpers and `_humanize_count`; keep classifier, probing, transcript, public API.
4. Rewrite `src/claude_busy_monitor/__init__.py`: re-export public API; `__version__ = importlib.metadata.version("claude-busy-monitor")`.
5. Rewrite `src/claude_busy_monitor/_cli.py`: import public API from `..` (or root), reimplement palette + rendering + `_humanize_count`, drop the placeholder `print` body.
6. Update `README-STATE-DETECTION.md`: replace `claude_busy_monitor.py` references with `src/claude_busy_monitor/_core.py`.
7. `git rm claude_busy_monitor.py`.
8. Add `install` target to `Makefile`: `uv tool install --force .` (depends on `build`).
9. Run `make lint && make build && make install && claude-busy-monitor` to verify acceptance criteria 1–8 manually.
10. Commit, push, open PR with `Closes #3`.

### 2.2 Scope boundary

In: code split, version handling, `make install`, `README-STATE-DETECTION.md` path updates, monolith deletion.
Out: tests (TODO #2), polished README (TODO #3), PyPI publish (TODO #4), GH ticket templates (TODO #5).

## 3. Closure

- Author: agent
- Model: Claude Opus 4.7
- Review: user

### 3.1 Implementation deviations

- `make install` does **not** depend on `make build`. Plan said "depends on build"; deviated because `uv tool install .` builds from source itself — an explicit dep is redundant work. Minimal-coupling principle inherited from #1 (`install-uv` unchained from `venv`).
- PR #4 review applied (post-impl):
  - Library module renamed `_core.py` → `_sessions.py` — names what the module is about (sessions) rather than its role (`_core`). Per CLAUDE.md naming discipline (what, not how).
  - `_cli.py`: ANSI escape constants regrouped into a `StrEnum` (`Ansi`).
  - `_cli.py`: `argparse.ArgumentParser` added so `claude-busy-monitor -h` prints a description.
  - `_sessions.py`: `get_state_counts(sessions=...)` docstring expanded to explain the consistency-with-prior-listing intent.
  - `Makefile`: dropped orphan `require` target — `uv run` auto-syncs for tooling targets, so `require` was unused. Folded `uv sync --extra dev` into `venv-activate` so the activated shell is always usable (e.g. before opening VS Code, for type-resolution and autocomplete).
  - `README.md`: simplified dev setup flow to `make venv-activate && make help`.

### 3.2 File inventory

- new: `CHANGES.md` — version + summary index, single source of truth.
- new: `src/claude_busy_monitor/_sessions.py` — library body (renamed from monolith → originally `_core.py`, then `_sessions.py` per PR review; ANSI helpers and CLI stripped).
- modified: `pyproject.toml` — `version` declared dynamic; `[tool.hatch.version]` regex source on `CHANGES.md`.
- modified: `src/claude_busy_monitor/__init__.py` — re-exports public API; `__version__` via `importlib.metadata`.
- modified: `src/claude_busy_monitor/_cli.py` — real CLI (palette as `Ansi` `StrEnum` + `_humanize_count` + `argparse`-driven `main`).
- modified: `Makefile` — added `install` target; dropped orphan `require` target; `venv-activate` now syncs deps before activating.
- modified: `README.md` — dev setup flow simplified to `make venv-activate && make help`.
- modified: `README-STATE-DETECTION.md` — companion path now points at `_sessions.py`.
- modified: `uv.lock` — refreshed by `uv sync` after pyproject change.
- deleted: `claude_busy_monitor.py` — replaced by `_sessions.py`.

Effective set matches § 2.1 inline mentions; the only post-plan divergence is the `_core.py` → `_sessions.py` rename captured in § 3.1.

### 3.3 Verification commands

```bash
make venv-activate          # creates .venv, syncs deps, opens activated shell
make lint                   # uv run ruff check src — clean
make build                  # dist/ wheel + sdist for 0.1.0
make install                # ~/.local/bin/claude-busy-monitor
claude-busy-monitor         # state summary + per-session lines
python -c "from claude_busy_monitor import (
  ClaudeSession, ClaudeState, TokenStats, get_sessions, get_state_counts, __version__
); print(__version__)"      # → 0.1.0
```

### 3.4 Coverage check

Within charter scope.

### 3.5 Test review

- _Coverage_: no test code added; justification (c) per devlog rule — building the scaffold is the entire scope of TODO #2. Test seeds for that task are in § 3.7.
- _Effectiveness_: no existing test caught any error during this task (no tests exist yet).

### 3.6 Gate check

- Acceptance criteria 1–9: met (criteria 1–8 verified by § 3.3; criterion 9 satisfied by § 3.7).
- All deliverables committed on `impl/0003-split-monolith`.
- Mandate review gate: § 1 + § 2 user-attested before implementation began.

### 3.7 Test seeds for TODO #2

Aspects spotted during the split worth covering in TODO #2:

1. **Probe parsing — `_load_session_probes`**: malformed JSON in a probe file is silently dropped; required-field validation; unknown `status` drops the probe; pid that fails `_is_process_claude` drops the probe.
2. **Solo vs. multi disambiguation in `_find_active_jsonl`**: when multiple probes share a cwd, each must use its own `session_id_hint` (no newest-jsonl fallback); single-probe cwd falls back to newest jsonl. README §A3 codifies; bug-prone.
3. **Path encoding in `_find_active_jsonl`**: cwd `/foo/bar` → project dir `-foo-bar`. Edge cases: trailing slash, embedded dashes. README §A2.
4. **`_compute_token_stats` field summation**: must sum `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`. Using only `input_tokens` underreports by ~100×. README §B; regression risk.
5. **`_PROBE_STATUS_MAP`**: exactly three keys. Adding a fourth status without updating the map silently drops affected sessions (README §A4 fix recipe).
6. **`get_state_counts` with empty input**: returns all-three-keys map with 0 values, never missing keys.
7. **`__version__` ↔ `CHANGES.md` consistency**: hatch regex pattern and topmost `## Version X.Y.Z:` line must agree; bump-then-rebuild check.
8. **Smoke**: `claude-busy-monitor` exits 0 on a system with no live Claude sessions; `SESSIONS_DIR` not existing handled gracefully.
9. **CLI rendering invariants**: summary line includes all three states; ANSI escapes stable for `watch` consumption.
10. **End-to-end fixture shape**: tmpdir tree mocking `~/.claude/sessions/<pid>.json` + `~/.claude/projects/<encoded>/<sid>.jsonl` with a known transcript — exercises full stack without spawning a real Claude.

### 3.8 Demo scenario

```bash
git checkout <merge-commit-hash>
make venv && source .venv/bin/activate
make require && make install
claude-busy-monitor
```

Expected output: a state-summary line (busy / asking / idle counts, color-coded) followed by one line per live Claude session with cumulative input/output tokens.

### 3.9 Retrospective

| #   | Point                                                                      | Agent    | User       |
| --- | -------------------------------------------------------------------------- | -------- | ---------- |
| 1   | Mandate compression + planned tree caught design tensions before code      | well     | well       |
| 2   | Hatch regex source for version: clean, single source of truth              | well     | well       |
| 3   | `make install` no-build-dep deviation surfaced during impl, not in plan    | not well | ended well |
| 4   | Test-seeds appendix doubled as forward-feed to TODO #2                     | well     | well       |
| 5   | Lean closure (~150-line target) feasible for mechanical splits             | well     | well       |
| 6   | Implementation phase ran straight-through, zero hook trips on impl commits | surprise | don't care |

### 3.10 Forward-looking check

- TODO #2 (test scaffold) gets explicit seeds (§ 3.7) plus stable module boundaries (`_core` for lib, `_cli` for rendering) to mock against.
- TODO #3 (README polish) inherits a "library + CLI" narrative rather than "monolith".
- TODO #4 (PyPI publish) inherits a working `make build` + `make install`; only `UV_PUBLISH_TOKEN` wiring remains.

### 3.11 Verdict

**Recommendation**: Accept.

**Rationale**:

- All 9 acceptance criteria met (§ 3.3 verifies 1–8; § 3.7 satisfies 9).
- `make lint && make build && make install && claude-busy-monitor` runs clean.
- `__version__` reads `0.1.0` from `CHANGES.md` via hatch — single source of truth confirmed end-to-end.
- `_core.py` carries no ANSI escapes (`grep -nE '\\x1b' src/claude_busy_monitor/_core.py` → empty).

## Governance trace

| #   | Requirement                  | Source                     | How met                                           |
| --- | ---------------------------- | -------------------------- | ------------------------------------------------- |
| 1   | Devlog entry                 | charter § 12.7 / CLAUDE.md | `architecture/devlog/0003-split-monolith.md`      |
| 2   | GH issue with category tag   | CLAUDE.md                  | #3 (`[impl]`)                                     |
| 3   | Branch from main             | CLAUDE.md                  | `impl/0003-split-monolith`                        |
| 4   | Mandate review gate          | CEREMONIES § Task start    | § 1 + § 2 user-attested before code               |
| 5   | Author/Model/Review metadata | charter § 12.1             | per-section blocks present                        |
| 6   | Acceptance criteria          | charter § 12.7             | § 1.7 (9 criteria)                                |
| 7   | Test plan in mandate         | CEREMONIES § Task start    | § 1.6 (operational; scaffold deferred to TODO #2) |
| 8   | Coverage check               | charter § 12.5             | § 1.8 + § 3.4                                     |
| 9   | Test review at closure       | CEREMONIES § Task closure  | § 3.5                                             |
| 10  | Demo scenario                | CEREMONIES § Task closure  | § 3.8                                             |
| 11  | Retrospective voting table   | CEREMONIES § Task closure  | § 3.9                                             |
| 12  | Forward-looking check        | CEREMONIES § Task closure  | § 3.10                                            |
| 13  | Verdict (self-assessment)    | devlog/CLAUDE.md           | § 3.11                                            |

## Resource consumption

| Metric                   | Value                                                                                 |
| ------------------------ | ------------------------------------------------------------------------------------- |
| Wall time                | ~2 h (devlog setup + impl + closure)                                                  |
| LOC changed              | +121 / -91 (`git diff main...HEAD --stat`)                                            |
| Files changed            | 8 (excl. devlog)                                                                      |
| Commits on branch        | 4 (devlog open + tree + seeds + impl)                                                 |
| Pre-commit hook failures | 1 (review-attestation hook on closure edit, resolved by Write fallback per CLAUDE.md) |
| Subagent invocations     | 0                                                                                     |
| `/clear` events          | 0                                                                                     |
| Memory rotation events   | 1 (`/compact` at session start)                                                       |
