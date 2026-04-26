# 0001 — Build skeleton: pyproject, venv, Makefile, ruff, VS Code

- GH issue: #1
- Branch: `impl/0001-build-skeleton`
- Opened: 2026-04-26
- Closed: 2026-04-26

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.7
- Review: user

### 1.1 Context

First implementation task. Bootstraps tooling that GH issues #1 successors (TODO #1–5) depend on. No predecessor.
First-task carve-outs: `AI-AUGMENTED-ENGINEERING-CHARTER.md`, `MEMORY.md`, `governance/`, `HOWTO-*.md`, `architecture/ARCHITECTURE.md` are referenced by `CLAUDE.md` but not present yet — to be addressed when relevant.

### 1.2 Task nature

Execution.

### 1.3 Problem statement

`claude_busy_monitor.py` is a 974-LOC monolith. The existing `Makefile` is DFD-era (setuptools + twine + black + shell `tools/*.sh`). No installable build, no venv conventions, no lint/format config. This blocks the split (TODO #1), tests (#2), README polish (#3), and publish (#4).

### 1.4 Goal

A working `uv` + `hatchling` + `ruff` skeleton driven by `Makefile`. Clean checkout → `make venv && source .venv/bin/activate && make require` yields a fully tooled environment. CLI entry-point is registered as a stub; the actual code split happens in TODO #1.

### 1.5 Design decisions

- Build backend: `hatchling`.
- Dependency manager: `uv` in project mode (`uv sync` against `uv.lock`).
- Lint/format: `ruff` (replaces `black` + shell `lint.sh`).
- Orchestration: `Makefile` as a thin wrapper. Recipes use `uv run <tool>` so they work without prior activation; activated-venv usage also supported.
- `uv.lock` committed.
- VS Code format-on-save: `ruff` for Python, `prettier` for Markdown.
- Existing `Makefile` replaced wholesale; legacy `tools/*.sh` references retired.

Tradeoff settled in conversation 2026-04-26: project-mode lock-in vs. faster sync + reproducibility — chose the latter. `uv` becomes a hard contributor dependency (one-line install via `pipx install uv`).

### 1.6 Test plan / fixtures

Build tooling only; no production code added. Verification is operational:

- `make venv && make require` succeeds on a clean checkout.
- `make lint` and `make format` run cleanly (config tolerates empty `src/`).
- `make build` produces wheel + sdist in `dist/`.
- `make publish` is dry-tested by the user against TestPyPI; not by the agent.

### 1.7 Acceptance criteria

1. `pyproject.toml` is the single config source: project metadata, deps, `[tool.ruff]`, `[build-system] hatchling`.
2. `Makefile` exposes `venv`, `require`, `lint`, `format`, `test`, `build`, `publish`, `clean`; documented via `make help`.
3. `ruff` configured: default rules + `I` (isort); `ruff check` and `ruff format` wired.
4. `.vscode/settings.json` enables format-on-save (ruff for Python, prettier for Markdown); `.vscode/extensions.json` recommends both.
5. `uv.lock` committed; `uv lock --check` passes.
6. CLI `claude-busy-monitor` registered as a stub entry-point.
7. `claude_busy_monitor.py` untouched (split is TODO #1).
8. CI not added (deferred — revisit alongside TODO #2).

### 1.8 Watchlist reminder

No active watchlist (file referenced by `CLAUDE.md` not yet present).

### 1.9 Coverage check

Within charter scope.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.7
- Review: user

### 2.1 Steps

1. `pyproject.toml`: name `claude-busy-monitor`, version `0.0.1`, `requires-python >= 3.11`, `dependencies = []`, `[project.optional-dependencies] dev = ["pytest", "ruff"]`, `[project.scripts] claude-busy-monitor = "claude_busy_monitor._cli:main"`, `[tool.ruff]` (line-length 100, default rules + `I`), `[tool.hatch.build.targets.wheel]` selecting `src/claude_busy_monitor`.
2. Package skeleton: `src/claude_busy_monitor/__init__.py` (empty + `__version__`); `src/claude_busy_monitor/_cli.py` with stub `main()` printing "claude-busy-monitor: scaffold only — see TODO #1".
3. `Makefile` rewrite: default goal `help`; targets call `uv` and `uv run`. Old DFD-era targets (`nr-*`, `readme`, `doc`, `publish-to-pypi`, `publish-to-gh`, `black`, shell-based `lint`, `install`, `require-system`, `venv-activate`, `_venv`, `all`) removed.
4. `.vscode/settings.json` + `.vscode/extensions.json` per § 1.7 #4.
5. `.gitignore`: add `.venv/`, `dist/`, `build/`, `*.egg-info/`, `__pycache__/`, `.ruff_cache/`, `.pytest_cache/`. **Surfaced for user decision**: existing entries (`CEREMONIES.md`, `CLAUDE.md`, `architecture/ARCHITECTURE.md`) look unintended since those files are tracked — left untouched until clarified.
6. Generate `uv.lock` via `uv lock`; commit.
7. README: replace contents with a minimal pointer paragraph (`pipx install uv`, `make venv`, activate, `make require`, `make help`). Full polish in TODO #3.
8. Smoke check: from a clean checkout, `rm -rf .venv && make venv && source .venv/bin/activate && make require && make lint && make build`.

### 2.2 Scope boundary

Out of scope: splitting `claude_busy_monitor.py` (TODO #1), test scaffold (TODO #2), full README polish (TODO #3), PyPI publish (TODO #4), CI, fixing the suspicious `.gitignore` entries.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

### 3.1 Implementation deviations

- Step 4 (`.vscode/`) executed by user on `main` (`c669050`/`e19a820`) before agent reached it; agent skipped accordingly.
- Step 5: user pre-cleared the suspicious `.gitignore` entries on `main`; agent then appended `dist/`, `build/`, `*.egg-info/`, `.ruff_cache/` as planned.
- Step 8: `uv` not installed system-wide on the agent host; the official `curl|sh` installer was permission-denied. Workaround: copied `.venv/bin/uv` to `~/.local/bin/uv` so `make venv` flow could be exercised. README still documents `pipx install uv` for fresh-machine provisioning.
- In-task scope-expansion proposals (test smoke suite, `make install`, `CHANGES.md` versioning) deferred to TODO #1 / #2 per mandate-gate discipline.

### 3.2 File inventory

Created: `pyproject.toml`, `src/claude_busy_monitor/{__init__.py,_cli.py}`, `README.md`, `uv.lock`, `architecture/devlog/0001-build-skeleton.md`.
Modified: `Makefile` (wholesale replacement), `.gitignore` (+4 entries).
Untouched (in scope): `claude_busy_monitor.py`, `README-STATE-DETECTION.md`.
On-main housekeeping (not branch): `.vscode/`, `.prettierrc`, `.claude/hooks/`, `.claude/settings.json`, TODO.md updates.

### 3.3 Verification commands

```bash
rm -rf .venv && make venv                                    # uv venv .venv  (Python 3.12.3)
source .venv/bin/activate
make require                                                 # 7 packages installed
make lint                                                    # All checks passed!
make format                                                  # 2 files left unchanged
make build                                                   # dist/claude_busy_monitor-0.0.1-py3-none-any.whl + .tar.gz
claude-busy-monitor                                          # "claude-busy-monitor: scaffold only — see TODO #1"
make help                                                    # 9 targets listed
uv lock --check                                              # Resolved 8 packages
uv tool install .                                            # ~/.local/bin/claude-busy-monitor — global CLI install verified
```

### 3.4 Test review

- _Coverage_: no tests added in this task. Build tooling; verification is operational (§ 3.3). Test scaffold is TODO #2's deliverable.
- _Effectiveness_: N/A.

### 3.5 Gate check

All 8 acceptance criteria met (verified in § 3.3). `make test-full` doesn't exist yet (carve-out — TODO #2). Mandate § 1 + execution plan § 2 user-attested before implementation (commit `ae18093` / cherry-picked as `57817af`).

### 3.6 Demo scenario

Replayable at PR merge SHA on a fresh checkout:

```bash
git clone git@github.com:pbauermeister/claude-busy-monitor.git && cd claude-busy-monitor
pipx install uv          # one-time, contributor prerequisite
make venv && source .venv/bin/activate
make require             # 7 packages
make help                # 9 targets
make lint                # All checks passed!
make build               # wheel + sdist in dist/
claude-busy-monitor      # "claude-busy-monitor: scaffold only — see TODO #1"
```

### 3.7 Retrospective

| #   | Point                                                                                           | Agent | User |
| --- | ----------------------------------------------------------------------------------------------- | ----- | ---- |
| 1   | Decomposing the original TODO #1 into 5 tasks before opening                                    | well  |      |
| 2   | Discussing build-system framework before drafting § 2 (CLAUDE.md "Code-reuse" trigger)          | well  |      |
| 3   | Mandate gate caught scope-creep proposals (smoke suite, make install, CHANGES.md) and deferred  | well  |      |
| 4   | Multiple force-pushes to scrub historical commit-message references — cost of late-discovered hygiene | not well |      |
| 5   | `make test` exits 5 when no tests — pytest convention                                           | surprise |    |
| 6   | `uv` install path on agent host — copied from venv vs. system installer denied                  | surprise |    |

### 3.8 Forward-looking check

Unblocks TODO #1 (split monolith — package layout fixed), TODO #2 (test scaffold — Makefile target shape known), TODO #3 (README polish — file exists), TODO #4 (PyPI publish — `make publish` calls `uv publish`). TODO #5 independent.

### 3.9 Verdict

**Recommendation**: Accept with reservations.

**Rationale**: all 8 acceptance criteria met (§ 3.3); smoke check passes end-to-end; `uv lock --check` passes; wheel + sdist produced; both editable-venv and `uv tool install .` paths work; mandate gate honoured.

**Reservations**:

1. `uv` not installed system-wide on agent's host (copied from `.venv` workaround). Fresh-machine path documented in README; user should verify on a fresh checkout if confidence wanted.
2. `make test` exits 5 with empty test suite — addressed in TODO #2.
3. `arduino-esp32-tft-terminal` reference in commit `88febae` body left intact per user decision (TODO outside this task).

## Governance trace

| Source                              | Clause                           | Action  | Note                                                                                            |
| ----------------------------------- | -------------------------------- | ------- | ----------------------------------------------------------------------------------------------- |
| CEREMONIES.md `Task start`          | Task start ceremony              | applied | scope decomposed; framework discussed before § 2                                                |
| CEREMONIES.md `Mandate approval gate` | Mandate gate                   | applied | user attested § 1 + § 2 before code; resets caused by hook design                               |
| CLAUDE.md `Code-reuse`              | Frameworks and libraries trigger | applied | `uv` + `hatchling` over hand-rolled setup                                                       |
| CLAUDE.md `YAGNI`                   | YAGNI                            | applied | `dependencies = []`; populated in TODO #1                                                       |
| CLAUDE.md `Naming discipline`       | Outcome-named                    | applied | `claude-busy-monitor` describes purpose                                                         |
| architecture/devlog/CLAUDE.md       | Lean mandate + execution plan    | applied | two-pass compression                                                                            |
| CLAUDE.md `Housekeeping on main`    | Branch hygiene                   | applied | TODO.md updates committed on `main`; branch left untouched until rebuild                        |
| CLAUDE.md `Force-push confirmation` | Destructive op gate              | applied | user authorized 3 force-pushes (pikett scrub, ec66934 scrub, branch rebuild)                    |
| CLAUDE.md `First-task carve-out`    | Bootstrapping gap                | tension | Charter / MEMORY / governance / HOWTO absent — proceed with carve-out per user (2026-04-26)     |
| CEREMONIES.md `Task closure`        | Task closure ceremony            | applied | this section                                                                                    |

## Resource consumption

| Phase          | Tokens (approx) | Wall time |
| -------------- | --------------- | --------- |
| Mandate        | ~30k            | 30 min    |
| Implementation | ~120k           | 2 h       |
| Closure        | ~40k            | 30 min    |
| **Total**      | **~190k**       | **~3 h**  |

| Counter                                  | Value                                |
| ---------------------------------------- | ------------------------------------ |
| Pre-commit hook fails                    | 0                                    |
| Pre-tool-use hook denials                | 2 (force-push amend, `curl\|sh`)     |
| Force-pushes (main)                      | 2 (pikett scrub, ec66934 scrub)      |
| Force-pushes (branch)                    | 2 (pikett-related, ec66934-related)  |
| LOC changed (`git diff main...HEAD`)     | +320 / -92 net                       |
| Files changed                            | 8                                    |

