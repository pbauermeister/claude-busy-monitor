# 0001 — Build skeleton: pyproject, venv, Makefile, ruff, VS Code

- GH issue: #1
- Branch: `impl/0001-build-skeleton`
- Opened: 2026-04-26

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

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
- Review: pending

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

## Governance trace

| Source                           | Clause                          | Action  | Note                                           |
| -------------------------------- | ------------------------------- | ------- | ---------------------------------------------- |
| CEREMONIES.md `Task start`       | Task start ceremony             | applied | scope decomposed; framework discussed before § 2 |
| CLAUDE.md `Code-reuse`           | Frameworks and libraries trigger | applied | `uv` + `hatchling` over hand-rolled setup     |
| CLAUDE.md `YAGNI`                | YAGNI                           | applied | `dependencies = []`; populated in TODO #1     |
| CLAUDE.md `Naming discipline`    | Outcome-named                   | applied | `claude-busy-monitor` describes purpose       |
| architecture/devlog/CLAUDE.md    | Lean mandate + execution plan   | applied | two-pass compression                           |
| CLAUDE.md `First-task carve-out` | Bootstrapping gap               | tension | Charter / MEMORY / governance / HOWTO absent — proceed with carve-out per user (2026-04-26) |

## Resource consumption

_(filled at closure)_

## Factoring candidates

_(none yet)_
