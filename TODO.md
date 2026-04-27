# TODO

Recognized tasks are recorded as GitHub issues and managed in detail in corresponding `<folder>/devlog/NNNN-*.md` files.

This file captures items as they arise during work, so nothing is forgotten without diverting the current discussion or reasoning. Items collected here can later be specified as tasks, grouped together, or discarded. If a TODO item becomes significant effort, it must be turned into a standard task (GH ticket, PR, devlog).

## Won't

## TODO Items

### 1. Revisit publish/release tooling

Hand-rolled in #9 + #11: `scripts/publish-preflight.sh`, `make publish-quality`, `make publish-tag`, `HOWTO-PUBLISH.md`. Total ~250 LOC. Per CLAUDE.md `Code-reuse: frameworks and libraries`, this should have been considered at #9 mandate time — publishing/release management is a known solved space:

- `python-semantic-release` — Conventional-Commits-driven version + changelog + tag + publish.
- `release-please` (Google) — opens release PR with bump + changelog; tag + publish on merge.
- `pypa/gh-action-pypi-publish` — OIDC trusted publishing from GitHub Actions, no token.
- `commitizen`, `bump-my-version` — narrower (bump + tag only).
- `twine check dist/*` — PyPI README rendering check (would have caught the v0.1.0 hero-image-on-PyPI bug).

Decision deferred to a tooling-audit task: stay hand-rolled (local-only, full uninstall/reinstall cycle is unusual and valuable) vs migrate (CI + OIDC is the modern shape, less surface to maintain). For now, low-hanging fruit only: add `uvx twine check dist/*` to `make publish-quality`.

**Streamlining angle** — the Makefile is ~225 LOC across ~25 targets in 4 user-facing groups (Quality, Tests, Build and install, Publish to PyPI). For a single-CLI / no-deps project this is a lot of boilerplate. Audit candidates: drop legacy install/uninstall targets if unused in practice, fold rarely-invoked targets into others, consider whether `pyproject.toml` script entries or hatch-build hooks could replace Makefile recipes. Goal: cut ~50% LOC while keeping the gate semantics (`publish-quality` cycle is the keeper).

**Prerequisite for removing `install-legacy` / `uninstall-legacy`**: the dependent project `arduino-esp32-tft-terminal` must first be made venv-compliant. It currently relies on the user-wide pip install (the "temporary hack" of Makefile note (2)) to import `claude-busy-monitor` as a library. Once it activates a venv and installs from PyPI, the legacy targets become removable.

**Slim post-publish verifier** — `make publish-verify` running `uvx --from "claude-busy-monitor==$VERSION" claude-busy-monitor --version` to confirm PyPI propagation + wheel installability in a throwaway env. ~10 lines, ~10 seconds. Heavy version (full smoke suite from PyPI install) is overkill for this project (no deps, single entry, same install codepath as local).

### 2. Install template for GH tickets (bug, feature request)

Gradually use GH tickets instead of TODO.md.

Later features include:

- Extract classification documentation from Python code comment sections to a separate README.
- Clarify that the classification is based on empirical findings, Claude Code version-dependant.
- Currently works for Linux. OSX support to be envisaged.
- Currently works with Claude Code v2.1.119. Version compatibility to be discussed.
