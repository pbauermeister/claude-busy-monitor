# TODO

Recognized tasks are recorded as GitHub issues and managed in detail in corresponding `<folder>/devlog/NNNN-*.md` files.

This file captures items as they arise during work, so nothing is forgotten without diverting the current discussion or reasoning. Items collected here can later be specified as tasks, grouped together, or discarded. If a TODO item becomes significant effort, it must be turned into a standard task (GH ticket, PR, devlog).

## Won't

## TODO Items

### 1. Revisit publish/release tooling

Hand-rolled in #9 + #11: `scripts/publish-preflight.sh`, `scripts/publish-tag.sh`, `make publish-quality`, `HOWTO-PUBLISH.md`. ~250 LOC for a single-CLI / no-deps project. Per CLAUDE.md `Code-reuse: frameworks and libraries`, should have been considered at #9 mandate time.

**Direction settled** — streamline using off-the-shelf tools where they fit; **keep the manual gate before publish**. Auto-publish from CI is off the table because:

- claude-busy-monitor: live Claude Code E2E is brittle (cost, non-determinism, CC session-file format drift); synthetic-probe tests cover the parser layer but not "did the published artefact really work end-to-end".
- arduino-esp32-tft-terminal: firmware E2E is tractable via emulators (wokwi for ESP32) up to display-output verification, which still needs manual visual check.

**Candidates that fit the manual-gate model**:

- `twine check dist/*` — PyPI README rendering check. Would have caught the v0.1.0 hero-URL bug. Cheapest near-term win — fold into `publish-quality`.
- `bump-my-version` / `commitizen` — version bump + tag (narrow scope; pairs with manual publish).
- `uvx --from "<pkg>==<ver>"` — slim `publish-verify` post-publish smoke (see below).

**Off the table** (CI-driven full pipelines, ruled out by manual-gate stance; listed for completeness): `python-semantic-release`, `release-please`, `pypa/gh-action-pypi-publish`.

**Streamlining angle** — Makefile is ~225 LOC across ~25 targets in 4 user-facing groups. For a single-CLI / no-deps project this is a lot of boilerplate. Audit candidates: drop legacy install/uninstall (see prereq below), fold rarely-invoked targets, consider `pyproject.toml` script entries or hatch-build hooks. Goal: ~50% LOC cut while keeping `publish-quality` cycle semantics.

**Prerequisite for removing `install-legacy` / `uninstall-legacy`**: dependent project `arduino-esp32-tft-terminal` must first be made venv-compliant — currently relies on the user-wide pip install (Makefile note (2)) to import `claude-busy-monitor` as a library.

**Slim post-publish verifier** — `make publish-verify` running `uvx --from "claude-busy-monitor==$VERSION" claude-busy-monitor --version` to confirm PyPI propagation + wheel installability in a throwaway env. ~10 lines, ~10 seconds. Heavy version (full smoke suite from PyPI install) is overkill (no deps, single entry, same install codepath as local).

**Separately** (independent of the publish workflow): PR-validation CI (lint + unit + smoke on push; **no** auto-publish) is a different concern — catches regressions earlier than local `make check`. Worth its own ticket if pursued.

### 2. Install template for GH tickets (bug, feature request)

Gradually use GH tickets instead of TODO.md.

Later features include:

- Extract classification documentation from Python code comment sections to a separate README.
- Clarify that the classification is based on empirical findings, Claude Code version-dependant.
- Currently works for Linux. OSX support to be envisaged.
- Currently works with Claude Code v2.1.119. Version compatibility to be discussed.
