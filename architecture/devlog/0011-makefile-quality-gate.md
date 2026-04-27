# 0011 — Makefile quality gate

- GH issue: #11
- Branch: `impl/0011-makefile-quality-gate`
- Opened: 2026-04-27
- Closed: _(filled at closure)_

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

### 1.1 Context

Predecessor of #9 (PyPI publish workflow). #9 paused at PR #10 with the env-var bypass merged in. #9's HOWTO recommends a "max-quality before publish" sequence; this task introduces the primitive `make publish-quality` that the HOWTO will then call. Today's `Makefile` mixes depths (`check` → `test-full` → `test-unit`/`test-smoke`; `publish` recipe submakes preflight + build + publish), making the dep graph hard to follow.

### 1.2 Task nature

Execution. Refactor + small CLI addition + new high-level target. All locally testable.

### 1.3 Design decisions

- **Two-level model** (user spec): low-level targets have no other-target deps and do one thing; high-level targets compose low-levels only — no nesting, no high→high. `test-full` retained as a high-level peer (user choice — "we'll see if we need it").
- **Reclassification**: `build` flattens to low-level (no `lint` dep); `publish` flattens to bare `uv publish` (no embedded preflight/build); composition lives in `publish-quality`.
- **Postconditions** inline in Makefile recipes (~5 lines each, no script extraction): `verify-uninstalled` asserts `~/.local/bin/claude-busy-monitor` absent; `verify-installed` asserts present + executable + `--version` matches `CHANGES.md` topmost `## Version X.Y.Z:`. Absolute path bypasses `$PATH` ambiguity (avoids false-pass from a stray earlier install or PATH ordering).
- **CLI `--version`**: one new `add_argument("--version", action="version", version=__version__)` line in `_cli.py`. Reads `__version__` (already exposed via `importlib.metadata` in `__init__.py`).
- **`publish-quality` is verification-only** — does NOT call `uv publish`. User-visible flow becomes `make publish-quality && make publish`. Reasoning: gives the user a checkpoint to see all gates green before committing to the irreversible upload.
- **`publish-quality` composition** (in order, halts on first failure): `lint` → `test-unit` → `test-smoke` → `build` → `uninstall` → `verify-uninstalled` → `clean` → `install` → `verify-installed` → `publish-preflight`. Note: `clean` after uninstall removes the local venv before reinstall, so the post-install verification runs against a freshly-built artefact, not stale bytecode.
- **`make publish` becomes unsafe by default** — accepted because `make publish-quality` is the documented safe entry; HOWTO update (in #9 follow-up) will reflect this.

### 1.4 Test plan

- _Unit_: new test for `--version` — invoke `claude_busy_monitor._cli.main` with `--version`, assert exit 0 + version string matches `__version__`.
- _Manual_: full `make publish-quality` invocation on this branch (with `PUBLISH_ALLOW_ANY_BRANCH=1` for the embedded preflight) — must complete green; outcome recorded in § 3.
- _Manual sanity_: per-target invocations of new `verify-installed` / `verify-uninstalled` to confirm exit codes + messages.
- No automated test for the postcondition Makefile recipes (per user — synthetic state can't authentically reproduce real install/uninstall behaviour).

### 1.5 Acceptance criteria

1. Every `Makefile` target is either low-level (no other-target deps; recipe does one thing) or high-level (deps + recipe call only low-levels). No high→high.
2. `make verify-uninstalled` exits 0 iff `~/.local/bin/claude-busy-monitor` absent; non-zero with a one-line cause otherwise.
3. `make verify-installed` exits 0 iff `~/.local/bin/claude-busy-monitor` present, executable, and `--version` output matches the topmost `## Version X.Y.Z:` in `CHANGES.md`; non-zero with a one-line cause otherwise.
4. `claude-busy-monitor --version` exits 0 and prints the package version.
5. `make publish-quality` runs the full composition in the documented order, halts on first failure, exits 0 only when every gate passes. Does not invoke `uv publish`.
6. `make check` green; existing test suite (now including the new `--version` unit test) passes.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

### 2.1 Steps

1. `_cli.py`: factor argparse setup to a variable + add `--version` action (one line). Verify by hand: `python -m claude_busy_monitor._cli --version`.
2. `tests/unit/test_cli_version.py`: new test driving `main()` with `--version` (capture SystemExit + stdout).
3. `Makefile`: refactor to two-level model — flatten `build`, flatten `publish`, add `verify-installed`, `verify-uninstalled`, `publish-quality`. Update `cycle` to use the new verifications.
4. Manual: `make publish-quality` on this branch (with `PUBLISH_ALLOW_ANY_BRANCH=1`); record outcome.
5. `make check` green; commit; PR with `Closes #11`.

### 2.2 Scope boundary

In: `_cli.py` (`--version`), `tests/unit/test_cli_version.py`, `Makefile` (refactor + new targets), devlog.
Out: e2e → demo rename (separate ticket), HOWTO-PUBLISH.md update (handled in #9 follow-up), `test` alias removal (degenerate composition kept for muscle memory).

## 3. Closure

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

## Governance trace

| Source                                | Clause              | Action  | Note                                                      |
| ------------------------------------- | ------------------- | ------- | --------------------------------------------------------- |
| CEREMONIES.md `Task start`            | Task start ceremony | applied | TODO #1 follow-up → GH #11 → branch + devlog mandate gate |
| CLAUDE.md `Moderate auto mode`        | Stop-and-ask        | applied | confirmed name + scope + verification approach pre-draft  |
| CLAUDE.md `YAGNI`                     | YAGNI               | applied | inline postconditions, no script extraction, no smoke test |
| CLAUDE.md `Naming discipline`         | Outcome-named       | applied | `verify-installed`/`verify-uninstalled`/`publish-quality` |
| CLAUDE.md `Scope discipline`          | Single-purpose task | applied | e2e → demo rename split off                               |

## Resource consumption
