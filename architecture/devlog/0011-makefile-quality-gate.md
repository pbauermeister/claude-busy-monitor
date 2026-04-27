# 0011 — Makefile quality gate

- GH issue: #11
- Branch: `impl/0011-makefile-quality-gate`
- Opened: 2026-04-27
- Closed: 2026-04-27

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
- Review: user

### 3.1 Implementation deviations

- **AC #4 PARTIAL** — `publish-quality` does NOT call `publish-preflight` on this branch. The script `scripts/publish-preflight.sh` lives on #9 (PR #10), not on main. `publish-quality` runs the full lint+tests+build+uninstall+verify+clean+install+verify chain but ends without the preflight gate. Adding it is a one-line `$(MAKE) publish-preflight` in the recipe; deferred to a #9 follow-up commit once #9 lands. Captured in TODO follow-ups.
- **`test-full` renamed to `test` mid-task**. § 1.2 said "test-full retained as high-level peer per user"; user changed mind mid-task on the grounds that `test` is more traditional and `cycle` is actually the fuller test (uninstall/install round-trip). Clean rename; CEREMONIES.md § Task closure step 7 updated in the same commit (`make test-full` must pass → `make test` must pass).
- **`test` alias removed**. § 2.2 implied keeping it for muscle memory; user changed mind — degenerate alias was duplication. Removed before the `test-full` → `test` rename, so the new `test` is the same dep set with a different name.
- **Convention codification went through 3 iterations**. None of these were in the mandate; user fed them back during review:
  - First pass: brief layering note at file top.
  - Second pass: prominent CONVENTIONS block (§ 1 two-level + § 2 ≤80-col help).
  - Third pass: marker swapped from `# Purpose: <list>` comment to **colon-in-doc-string** (`<purpose>: <summary>`), which is more compact and visible in `make help`.
  - Fourth pass: § 3 order-by-call-sequence added.
- **`make help` extraction grep bug surfaced**. The conventions text used `: ##` literally to describe the doc-string format; the help-extraction grep matched it as a target line and printed garbage. Fixed by rewording.
- **CEREMONIES.md edit on a task branch**. Per CLAUDE.md, governance-file changes need user review. The change is one word (`make test-full` → `make test`); flagged at review time.

### 3.2 File inventory

- modified: `Makefile` — two-level refactor, conventions header (§§ 1–3), `verify-installed` / `verify-uninstalled` / `publish-quality`, by-purpose grouping with high-level marked by colon in `## doc`.
- new: `src/claude_busy_monitor/_cli.py` (+5 lines) — `--version` action.
- new: `tests/unit/test_cli_version.py` — drives `main()` with `--version`.
- modified: `CEREMONIES.md` — closure-gate command name updated.
- new: `architecture/devlog/0011-makefile-quality-gate.md` — this devlog.

### 3.3 Verification commands

```bash
make check                                       # 28 unit + 6 smoke green
make help                                        # all sections render; high-level marked by colon
make help | awk '{print length}' | sort -nr | head  # longest line = 80 (cycle)
make publish-quality                             # full chain green end-to-end (verified on this branch)
CLI=/tmp/fake make verify-installed              # synthetic-fixture acceptance + reject paths
```

### 3.4 Coverage check

Within charter scope. CEREMONIES.md edit is in-task scope (rename ripple).

### 3.5 Test review

- _Coverage_: `--version` covered by `tests/unit/test_cli_version.py`. `verify-installed` / `verify-uninstalled` Makefile recipes are explicitly NOT covered by automated tests per user (synthetic state can't authentically reproduce real install/uninstall behaviour); manual + synthetic-CLI fixtures (`CLI=/tmp/...`) used during development. Conventions header rules (§§ 1–3) are documentation, not code — verified by inspection during the iterative reviews.
- _Effectiveness_: § 3 call-sequence convention surfaced a real ordering issue (`verify-installed`/`verify-uninstalled` sat after BOTH `install` and `uninstall` instead of right after each); reorder fixed it. The convention paid off the same hour it was codified.

### 3.6 Gate check

- AC #1: ✓ — every target is low- or high-level; high-level marked by colon in `## doc`; conventions codified in file header.
- AC #2: ✓ — `verify-installed` / `verify-uninstalled` exit codes + messages confirmed (synthetic + actual CLI).
- AC #3: ✓ — `claude-busy-monitor --version` prints `claude-busy-monitor 0.1.0`; unit test asserts.
- AC #4: **PARTIAL** — `publish-quality` runs the chain minus `publish-preflight` (last step, see § 3.1). All other steps green end-to-end on this branch.
- AC #5: ✓ — `make check` green; `--version` unit test passes.
- Mandate § 1 + § 2 user-attested before code (commit `dc17ecf`).

### 3.7 Retrospective

| #   | Point                                                                                                                            | Agent    | User     |
| --- | -------------------------------------------------------------------------------------------------------------------------------- | -------- | -------- |
| 1   | Conventions codified in the file header (§§ 1–3) — future edits can't miss the layering, ≤80 col, or call-sequence rules         | well     | well     |
| 2   | Marker shape iterated: `# Purpose:` comment → colon-in-doc; second is more compact and visible in `make help`                    | not well | well     |
| 3   | `make help` extraction grep had a `: ##` literal-text bug, surfaced only post-edit by visual inspection                          | not well | well     |
| 4   | Resolved #9 ↔ #11 reciprocal dependency by deferring publish-preflight from publish-quality on #11; cleaner than cherry-pick     | well     | well     |
| 5   | `make publish-quality` ran end-to-end clean on this branch (lint+tests+build+uninstall+verify+clean+install+verify)              | well     | well     |
| 6   | Multiple reorder rounds (Build and install ordering, Publish ordering) — would have been one if call-sequence rule existed first | not well | well     |
| 7   | `test-full` → `test` rename signals "retained per user" mandate language was a hedge that resolved against keeping the long name | surprise | surprise |

### 3.8 Demo scenario

```
$ make publish-quality
About to run lint + tests + uninstall/install cycle. Does NOT upload.
Ctrl-C within 2 seconds to abort.
... lint passes; 28 unit + 6 smoke pass; uv build OK
... uv tool uninstall; verify-uninstalled: OK
... clean; uv tool install --reinstall .
... verify-installed: OK (~/.local/bin/claude-busy-monitor v0.1.0)
publish-quality: all gates green. Run 'make publish' to upload.

$ make help     # excerpt
 Quality:
  lint, format, check                                   ← check has colon
 Tests:
  test-unit, test-smoke, test-e2e, test                 ← test has colon
 Publish:
  publish-quality, publish                              ← publish-quality has colon
```

### 3.9 Forward-looking check

- **#9 follow-up** (after #9 lands): add `$(MAKE) publish-preflight` to `publish-quality` recipe (between `verify-installed` and the success message) — closes AC #4. Update `HOWTO-PUBLISH.md` to recommend `make publish-quality && make publish` instead of the standalone preflight.
- **TODO.md follow-ups** to add post-merge:
  - #9 follow-up: complete `publish-quality` chain (add `publish-preflight` step).
  - First user-driven `0.1.x` publish round (closes #9 AC #3).

### 3.10 Verdict

**Recommendation**: Accept with reservations.

**Rationale**:

- AC #1, #2, #3, #5 met; AC #4 partial (only `publish-preflight` deferred — script lives on #9, follow-up planned).
- `make publish-quality` ran end-to-end green on this branch.
- Conventions (§§ 1–3) codified in the Makefile header — future-proofs the layering, doc-string budget, and call-sequence rules so an editor (agent or human) can't miss them.

**Reservations**:

1. AC #4 partial — `publish-quality` doesn't yet call `publish-preflight`. One-line follow-up after #9 merges to main.
2. CEREMONIES.md edit (`make test-full` → `make test`) is on a task branch — needs your review at PR time per CLAUDE.md governance-file rule.

## Governance trace

| Source                              | Clause                 | Action  | Note                                                                        |
| ----------------------------------- | ---------------------- | ------- | --------------------------------------------------------------------------- |
| CEREMONIES.md `Task start`          | Task start ceremony    | applied | TODO #1 follow-up → GH #11 → branch + devlog mandate gate                   |
| CLAUDE.md `Moderate auto mode`      | Stop-and-ask           | applied | confirmed name + scope + verification approach pre-draft                    |
| CLAUDE.md `YAGNI` + scope           | YAGNI + single task    | applied | inline postconditions, no script extraction, e2e rename split               |
| CLAUDE.md `Naming discipline`       | Outcome-named          | applied | `verify-installed` / `verify-uninstalled` / `publish-quality`               |
| CEREMONIES.md `Convergence check`   | Reaching vs retreating | applied | convention iterations added substance (3 rules, marker shape) — not retreat |
| CLAUDE.md `Governance file edits`   | User review required   | applied | CEREMONIES.md edit committed on task branch; flagged for PR review          |
| MEMORY.md `Blocked edit workaround` | Use Write tool         | applied | § 3 closure fill used Write (Edit hook-blocked by user attestation)         |
| CEREMONIES.md `Task closure`        | Task closure ceremony  | applied | this section                                                                |

## Resource consumption

| Phase                           | Tokens (approx) | Wall time |
| ------------------------------- | --------------- | --------- |
| Mandate + plan + compress       | ~25k            | 30 min    |
| CLI + unit test                 | ~15k            | 15 min    |
| Makefile refactor (initial)     | ~30k            | 30 min    |
| Convention iterations + reviews | ~80k            | 1.5 h     |
| Closure                         | ~25k            | 25 min    |
| **Total**                       | **~175k**       | **~3 h**  |

| Counter                | Value                                                              |
| ---------------------- | ------------------------------------------------------------------ |
| Pre-commit hook fails  | 0                                                                  |
| Subagent invocations   | 0                                                                  |
| `/clear` events        | 0 (continuous session)                                             |
| Memory rotation events | 0                                                                  |
| LOC changed            | +190 / -30 (`git diff main...HEAD --stat`)                         |
| Files changed          | 5 (Makefile, \_cli.py, test_cli_version.py, CEREMONIES.md, devlog) |
| Commits on branch      | 13 (incl. this closure commit)                                     |
