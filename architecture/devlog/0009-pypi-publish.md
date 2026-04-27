# 0009 — PyPI publish workflow

- GH issue: #9
- Branch: `impl/0009-pypi-publish`
- Opened: 2026-04-27
- Closed: _(filled at closure)_

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

### 1.1 Context

Root `TODO.md` § 1 items 1-2: Makefile `publish` ready for first real-PyPI invocation; user-only execution. Item 3 (alpha → stable) deferred. Today: `Makefile` `publish` is `uv publish` only; no HOWTO; `CHANGES.md` at 0.1.0.

### 1.2 Task nature

Execution. `make publish` itself is user-only; agent prepares + reviews; user iterates `0.1.x` rounds.

### 1.3 Design decisions

- Pre-flight in `make publish`: clean tree, branch `main`, tag `v$VERSION` absent local + origin. Version from `CHANGES.md` regex (same as `pyproject.toml`). Each guard exits before any network call.
- TestPyPI: skipped per scope discussion.
- Token in HOWTO (not Makefile-enforced): `UV_PUBLISH_TOKEN` env var or keyring (`UV_KEYRING_PROVIDER=subprocess`). `~/.pypirc` not read by `uv publish` (verified `uv 0.11.7 --help`).
- Tag _after_ a successful publish; pre-flight's tag-absent check doubles as "did you bump?".
- `HOWTO-PUBLISH.md` at repo root: Prerequisites, Pre-flight, Publish, Tag + push, Verify, Troubleshooting.

### 1.4 Test plan

Smoke test (`tests/smoke/`, tmp-git-repo fixture) asserts each guard fires; HOWTO via Prettier hook + manual cross-check; end-to-end publish is user-only, per-round outcomes recorded in § 3 across rounds.

### 1.5 Acceptance criteria

1. `make publish` rejects (one-line cause, before network): dirty tree, untracked tracked-path files, branch ≠ `main`, tag `v$VERSION` present.
2. `HOWTO-PUBLISH.md` covers token, pre-flight, publish, tag + push, fresh-venv install verification, troubleshooting.
3. ≥ 1 user-driven `0.1.x` round publishes successfully.
4. `make check` green; existing `uv publish` behaviour preserved when pre-flight passes.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

### 2.1 Steps

1. `Makefile`: version extract + four pre-flight guards + `uv publish`.
2. `HOWTO-PUBLISH.md` per § 1.3.
3. Smoke test: tmp-git-repo fixture asserts each guard.
4. `make check`; commit; PR with `Closes #9`.
5. User-driven rounds → outcomes in § 3; devlog closes when user signals "no more rounds".

## 3. Closure

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

## Governance trace

| Source                                 | Clause              | Action  | Note                                                     |
| -------------------------------------- | ------------------- | ------- | -------------------------------------------------------- |
| CEREMONIES.md `Task start`             | Task start ceremony | applied | TODO #1 → GH #9 → branch + devlog with mandate gate      |
| CLAUDE.md `Moderate auto mode`         | Stop-and-ask        | applied | proposed scope + TestPyPI question before creating issue |
| CLAUDE.md `YAGNI`                      | YAGNI               | applied | shell pre-flight, no Python helper; no TestPyPI; no CI   |
| CLAUDE.md `Confidence and attribution` | Verified facts      | applied | `uv publish --help` consulted re token storage           |

## Resource consumption
