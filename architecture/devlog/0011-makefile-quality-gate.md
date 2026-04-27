# 0011 — Makefile quality gate

- GH issue: #11
- Branch: `impl/0011-makefile-quality-gate`
- Opened: 2026-04-27
- Closed: _(filled at closure)_

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.7
- Review: user

### 1.1 Context

Execution task. Predecessor of #9 (PR #10 paused). #9's HOWTO needs a `make publish-quality` primitive that this task introduces. Today's `Makefile` mixes depths (`check` → `test-full` → unit/smoke; `publish` recipe submakes preflight + build + publish), hard to follow.

### 1.2 Design decisions

- Two-level model: low-level = no other-target deps, one thing; high-level composes low-levels only, no high→high. `test-full` retained as high-level peer per user.
- Reclassify: `build` flattens to low-level (no `lint` dep); `publish` flattens to bare `uv publish`. `make publish` is unsafe-by-default; HOWTO (in #9 follow-up) directs to `publish-quality` first.
- Postconditions inline (~5 lines each): `verify-uninstalled` asserts `~/.local/bin/claude-busy-monitor` absent; `verify-installed` asserts present + executable + `--version` matches `CHANGES.md` topmost. Absolute path bypasses `$PATH` ambiguity. Needs CLI `--version` (one-line `argparse action="version"` reading `__version__`).
- `publish-quality` is verification-only; user flow `make publish-quality && make publish` gives a checkpoint before irreversible upload.

### 1.3 Test plan

Unit test for `--version` (drive `main()`, assert exit 0 + version string). No automated tests for postcondition Makefile recipes per user — synthetic state can't authentically reproduce real install/uninstall. Manual `make publish-quality` on this branch with `PUBLISH_ALLOW_ANY_BRANCH=1`; outcome in § 3.

### 1.4 Acceptance criteria

1. Every Makefile target is low-level (no deps, one thing) or high-level (composes low-levels only). No high→high.
2. `make verify-uninstalled` / `verify-installed` exit 0 iff `~/.local/bin/claude-busy-monitor` is absent / present-with-matching-version; non-zero with one-line cause otherwise. Version vs `CHANGES.md` topmost `## Version X.Y.Z:`.
3. `claude-busy-monitor --version` exits 0 and prints the package version.
4. `make publish-quality` runs `lint` → `test-unit` → `test-smoke` → `build` → `uninstall` → `verify-uninstalled` → `clean` → `install` → `verify-installed` → `publish-preflight`. Halts on first failure; does not invoke `uv publish`. `make check` green.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.7
- Review: user

### 2.1 Steps

1. `_cli.py`: factor argparse to a variable + `--version` action.
2. `tests/unit/test_cli_version.py`: drive `main()` with `--version`.
3. `Makefile`: refactor to two-level — flatten `build`, flatten `publish`, add `verify-installed`, `verify-uninstalled`, `publish-quality`; update `cycle`.
4. Manual `make publish-quality` (with `PUBLISH_ALLOW_ANY_BRANCH=1`); record outcome. `make check`; commit; PR with `Closes #11`.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

## Governance trace

| Source                         | Clause              | Action  | Note                                                          |
| ------------------------------ | ------------------- | ------- | ------------------------------------------------------------- |
| CEREMONIES.md `Task start`     | Task start ceremony | applied | TODO #1 follow-up → GH #11 → branch + devlog mandate gate     |
| CLAUDE.md `Moderate auto mode` | Stop-and-ask        | applied | confirmed name + scope + verification approach pre-draft      |
| CLAUDE.md `YAGNI` + scope      | YAGNI + single task | applied | inline postconditions, no script extraction, e2e rename split |
| CLAUDE.md `Naming discipline`  | Outcome-named       | applied | `verify-installed`/`verify-uninstalled`/`publish-quality`     |

## Resource consumption
