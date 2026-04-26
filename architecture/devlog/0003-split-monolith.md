# 0003 — Split monolith into installable library + CLI

- GH issue: #3
- Branch: `impl/0003-split-monolith`
- Opened: 2026-04-26
- Closed: _(filled at closure)_

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

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

### 1.8 Coverage check

Within charter scope.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

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
- Review: pending

_(filled at closure)_

## Governance trace

_(filled at closure)_

## Resource consumption

_(filled at closure)_
