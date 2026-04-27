# TODO

Recognized tasks are recorded as GitHub issues and managed in detail in corresponding `<folder>/devlog/NNNN-*.md` files.

This file captures items as they arise during work, so nothing is forgotten without diverting the current discussion or reasoning. Items collected here can later be specified as tasks, grouped together, or discarded. If a TODO item becomes significant effort, it must be turned into a standard task (GH ticket, PR, devlog).

## Won't

## TODO Items

### 1. PyPI publish

1. Publication to PyPI via the `Makefile` `publish` target (added in GH #1).
2. May only be called/tested by the user.
3. Follow-up after publish + a soak window with real usage: bump status straight from `alpha` → stable (skip beta). README badge `status-alpha-orange` → `status-stable-brightgreen`; pyproject classifier `Development Status :: 3 - Alpha` → `5 - Production/Stable`; version `0.x` → `1.0.0`. Rationale: 5-name public API, semver covers any later break; Beta-as-middle-step adds ceremony without real safety. Trigger is API confidence, not the publish itself.

### 2. Revisit publish/release tooling

Hand-rolled in #9 + #11: `scripts/publish-preflight.sh`, `make publish-quality`, `make publish-tag`, `HOWTO-PUBLISH.md`. Total ~250 LOC. Per CLAUDE.md `Code-reuse: frameworks and libraries`, this should have been considered at #9 mandate time — publishing/release management is a known solved space:

- `python-semantic-release` — Conventional-Commits-driven version + changelog + tag + publish.
- `release-please` (Google) — opens release PR with bump + changelog; tag + publish on merge.
- `pypa/gh-action-pypi-publish` — OIDC trusted publishing from GitHub Actions, no token.
- `commitizen`, `bump-my-version` — narrower (bump + tag only).
- `twine check dist/*` — PyPI README rendering check (would have caught the v0.1.0 hero-image-on-PyPI bug).

Decision deferred to a tooling-audit task: stay hand-rolled (local-only, full uninstall/reinstall cycle is unusual and valuable) vs migrate (CI + OIDC is the modern shape, less surface to maintain). For now, low-hanging fruit only: add `uvx twine check dist/*` to `make publish-quality`.

### 3. Install template for GH tickets (bug, feature request)

Gradually use GH tickets instead of TODO.md.

Later features include:

- Extract classification documentation from Python code comment sections to a separate README.
- Clarify that the classification is based on empirical findings, Claude Code version-dependant.
- Currently works for Linux. OSX support to be envisaged.
- Currently works with Claude Code v2.1.119. Version compatibility to be discussed.
