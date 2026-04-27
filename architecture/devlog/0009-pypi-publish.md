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

Root `TODO.md` § 1 _PyPI publish_ items 1 and 2:

> 1. Publication to PyPI via the `Makefile` `publish` target (added in GH #1).
> 2. May only be called/tested by the user.

Item 3 (alpha → stable bump) is an explicit follow-up after publish + soak — out of scope.
Existing state: `Makefile` has a one-line `publish` target (`uv publish`) added in #1. No HOWTO. README mentions PyPI as roadmap (line 50). Version `0.1.0` ready in `CHANGES.md`.

### 1.2 Task nature

Execution. Defined deliverables. The actual `make publish` invocation is **user-only** by design (TODO item 2); agent prepares + reviews; user iterates rounds with `0.1.x` bumps.

### 1.3 Goal

Make `make publish` ready for first real-PyPI invocation: pre-flight guards against common pitfalls in the target itself, and a `HOWTO-PUBLISH.md` capturing the end-to-end procedure (token, publish, tag, verify).

### 1.4 Design decisions

- **Pre-flight guards in `make publish`** (fail-fast, no surprises mid-upload): clean working tree, branch is `main`, version tag (`v$VERSION`) absent locally and on origin. Version is read from `CHANGES.md` via the same regex `pyproject.toml` uses (single source of truth).
- **TestPyPI rehearsal**: skipped per scope discussion. User validates via real-PyPI rounds with `0.1.x` bumps.
- **Token storage**: documented in HOWTO; not enforced by Makefile. Recommended path is `UV_PUBLISH_TOKEN` env var (interactive default) or keyring (`UV_KEYRING_PROVIDER=subprocess`) for durability. `~/.pypirc` is **not** read by `uv publish` (verified against `uv 0.11.7 --help`).
- **Tagging policy**: HOWTO instructs the user to tag (`v$VERSION`) and push the tag _after_ a successful publish, so the tag exists iff PyPI accepted the artefact. Pre-flight rejects re-publishing a tagged version, which doubles as a "did you bump?" check.
- **Pre-flight implementation**: shell snippet inside the Makefile recipe (proportional to task — adding a Python helper would be over-engineering for ~5 checks). Each check echoes a clear failure reason and exits non-zero.
- **HOWTO scope**: covers prerequisites (PyPI account, token), one-shot procedure, post-publish verification (`pip install` in fresh venv), troubleshooting (common `uv publish` errors). No CI section (no CI yet).
- **Naming**: `HOWTO-PUBLISH.md` at repo root, alongside future `HOWTO-USE.md` (CEREMONIES.md § Task closure step 10 mentions one — not yet created).

### 1.5 Test plan

- _Unit/smoke_: pre-flight guards are shell logic — testable by invoking `make publish` in synthetic states (dirty tree, wrong branch, tag exists) and asserting it exits non-zero with the expected reason. Implement as a smoke test with a temporary git worktree fixture, not in the existing test categories (would otherwise pollute `tests/unit` with shell-driven cases).
- _HOWTO doc_: rendering check (Prettier hook) + manual cross-check that every command resolves and every link works.
- _End-to-end publish_: **user-only**. Outcome of each round (success / failure / what changed) recorded into § 3 Closure as the user iterates. Devlog stays open across rounds; closure attestation comes after the final round the user wants to capture.

### 1.6 Acceptance criteria

1. `make publish` rejects: dirty tree, untracked files in tracked paths, branch ≠ `main`, version tag (`v$VERSION`) already present locally or on `origin`.
2. Each rejection prints a one-line cause and exits non-zero before any network call.
3. `HOWTO-PUBLISH.md` documents: token setup (env var + keyring options), pre-flight (what the Makefile checks and why), `make publish` invocation, post-publish steps (`git tag v$VERSION && git push origin v$VERSION`), fresh-venv install verification, troubleshooting common `uv publish` errors.
4. At least one user-driven round of `make publish` (with a `0.1.x` bump) completes successfully — recorded in § 3.
5. `make check` green.
6. Existing publish target's behaviour preserved when pre-flight passes (still calls `uv publish` against default index).

### 1.7 Watchlist reminder

No active watchlist for this project.

### 1.8 Coverage check

Within charter scope.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

### 2.1 Steps

1. Add pre-flight guards to `Makefile` `publish` target — version extraction (same regex as pyproject), then four checks (clean tree, untracked tracked-path files, branch == main, tag absent local + origin).
2. Write `HOWTO-PUBLISH.md` at repo root — sections: Prerequisites, Pre-flight (what the target checks), Publish, Tag + push, Verify, Troubleshooting.
3. Add a smoke test that drives `make publish` in synthetic states (tmp git repo fixture) and asserts each guard fires. Lives under `tests/smoke/`.
4. Run `make check`; commit; open PR with `Closes #9`.
5. **User-driven rounds**: user invokes `make publish` with successive `0.1.x` bumps in `CHANGES.md`; each round's outcome captured in § 3.1 / § 3.7. Devlog closes after the user signals "no more rounds".
6. § 3 Closure: deviations, file inventory, demo, verdict.

### 2.2 Scope boundary

In: `Makefile` publish-target hardening, `HOWTO-PUBLISH.md`, smoke test, devlog.
Out: alpha → stable bump (TODO item 3), PyPI badge in README, CI/automation, TestPyPI target, Python rewrite of pre-flight, `HOWTO-USE.md` (separate task).

## 3. Closure

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

_(filled at closure)_

## Governance trace

| Source                                | Clause                | Action  | Note                                                          |
| ------------------------------------- | --------------------- | ------- | ------------------------------------------------------------- |
| CEREMONIES.md `Task start`            | Task start ceremony   | applied | TODO #1 → GH #9 → branch + devlog with mandate gate           |
| CLAUDE.md `Moderate auto mode`        | Stop-and-ask          | applied | proposed scope + TestPyPI question before creating issue      |
| CLAUDE.md `YAGNI`                     | YAGNI                 | applied | shell pre-flight, no Python helper; no TestPyPI; no CI        |
| CLAUDE.md `Confidence and attribution` | Verified facts        | applied | `uv publish --help` consulted before answering token-store Q  |

## Resource consumption

_(filled at closure)_
