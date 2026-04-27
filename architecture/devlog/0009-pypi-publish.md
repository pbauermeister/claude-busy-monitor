# 0009 — PyPI publish workflow

- GH issue: #9
- Branch: `impl/0009-pypi-publish`
- Opened: 2026-04-27
- Closed: 2026-04-27

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.7
- Review: user

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
- Review: user

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

### 3.1 Implementation deviations

- **5 guards, not 4** (mandate § 2.1 said "four pre-flight guards"). Counted the `CHANGES.md` version-extract as a guard since it has the same exit-with-cause contract. Flagged in commit message instead of resetting the § 2 attestation (form-level mismatch, not a meaning change).
- **Pre-flight extracted to `scripts/publish-preflight.sh`** (mandate said "shell snippet inside Makefile recipe"). Extraction was for testability — the smoke test invokes the script directly against tmp git repos; would have required Makefile copying otherwise. Behavior identical.
- **`PUBLISH_ALLOW_ANY_BRANCH` env-var bypass added mid-task** (user request). Branch != main + var unset prints a hint naming the env var; var set prints WARNING and continues to remaining four guards. Two new smoke cases (`test_preflight_rejects_wrong_branch` extended to assert hint; `test_preflight_bypasses_branch_check_with_env_var` for the bypass path).
- **Reciprocal dependency with #11 surfaced late**. Mandate framed #9 as "the publish workflow"; #11 as "Makefile quality gate (predecessor of #9)". Actual: they're peers — #9 provides `publish-preflight`, #11's `publish-quality` calls it. Resolved by merging #9 first; #11 rebases on new main. Captured in retrospective.

### 3.2 File inventory

- new: `scripts/publish-preflight.sh` — five guards, exit-with-cause, env-var bypass.
- new: `HOWTO-PUBLISH.md` — token storage, pre-flight table, publish/tag/verify, troubleshooting, § 2.1 bypass note.
- new: `tests/smoke/test_publish_preflight.py` — 8 cases (clean pass, missing CHANGES, wrong branch, bypass with env var, modified tree, untracked file, local tag, origin tag via bare-repo origin).
- modified: `Makefile` — `publish-preflight` target (manual sanity check); `publish` recipe runs pre-flight → build → `uv publish`.
- new: `architecture/devlog/0009-pypi-publish.md` — this devlog.

### 3.3 Verification commands

```bash
make check                                       # 27 unit + 14 smoke green
make publish-preflight                           # rejects on this branch with hint
PUBLISH_ALLOW_ANY_BRANCH=1 make publish-preflight  # WARNING + remaining guards run
npx prettier --check HOWTO-PUBLISH.md            # green
```

### 3.4 Coverage check

Within charter scope.

### 3.5 Test review

- _Coverage_: pre-flight script covered by 8-case smoke suite — each guard has at least one rejecting case; bypass has one accepting + one rejecting (other guards still fire). HOWTO is doc-only — no test (justified absence). The actual `uv publish` invocation is user-only (AC #3) — not testable in CI.
- _Effectiveness_: `test_preflight_rejects_modified_tree` initially failed because the test overwrote `CHANGES.md` (killing the version-extract guard before reaching dirty-tree). Fixed by appending instead of overwriting. Caught a test-author bug, not a script bug.

### 3.6 Gate check

- AC #1: ✓ (5-guard pre-flight, all tested).
- AC #2: ✓ (HOWTO covers token, pre-flight, publish, tag + push, fresh-venv install verification, troubleshooting).
- AC #3: **DEFERRED** — no real publish round yet; depends on user PyPI credential setup and is logically downstream of #11's `publish-quality` landing. Captured as TODO follow-up post-merge.
- AC #4: ✓ (`make check` green; `uv publish` behaviour preserved as the `publish` recipe's last step).
- Mandate § 1 + § 2 user-attested before code (commit `c70632b`).

### 3.7 Retrospective

| #   | Point                                                                                                                            | Agent    | User |
| --- | -------------------------------------------------------------------------------------------------------------------------------- | -------- | ---- |
| 1   | Verified `uv publish` token sources via `--help` before answering — kept the credential-storage answer grounded                  | well     | ?    |
| 2   | Pre-flight script extraction wasn't in the mandate but unlocked clean smoke testing — improvement on the planned shape           | well     | ?    |
| 3   | Plan said 4 guards, shipped 5 — flagged in commit instead of resetting attestation (form-level mismatch, not a meaning change)   | not well | ?    |
| 4   | `PUBLISH_ALLOW_ANY_BRANCH` added mid-task in response to actual workflow need (test publish without merging)                     | well     | ?    |
| 5   | Missed the #9 ↔ #11 reciprocal dependency at #11 mandate — surfaced only when about to write the Makefile refactor               | not well | ?    |
| 6   | Devlog compression hit a structural floor (104 → 70 = 67%); the 60% target proved unreachable without dropping mandated sections | surprise | ?    |

### 3.8 Demo scenario

```bash
# Reject with hint on non-main branch:
$ make publish-preflight
publish-preflight: branch must be 'main' (current: 'impl/0009-pypi-publish')
publish-preflight: hint — set PUBLISH_ALLOW_ANY_BRANCH=1 to bypass (intended for publish-process testing, not normal use)

# Bypass for testing the publish process itself:
$ PUBLISH_ALLOW_ANY_BRANCH=1 make publish-preflight
publish-preflight: WARNING — branch check bypassed (PUBLISH_ALLOW_ANY_BRANCH set, branch='impl/0009-pypi-publish')
publish-preflight: OK — ready to publish v0.1.0

# Smoke suite:
$ uv run pytest tests/smoke/test_publish_preflight.py -v
# 8 cases pass: clean, missing CHANGES, wrong branch, bypass, modified, untracked, local tag, origin tag
```

### 3.9 Forward-looking check

- **#11 (Makefile quality gate)** wraps `publish-preflight` in a higher-level `publish-quality` target. Order: this PR merges → #11 rebases on new main → #11 ships the gate.
- **HOWTO-PUBLISH.md update** post-#11: recommend `make publish-quality && make publish` as the safe entry, dropping the standalone `publish-preflight` callout from § 3 step 3.
- **TODO.md follow-ups** to add post-merge:
  - First user-driven `0.1.x` publish round + record outcome (closes AC #3).
  - HOWTO-PUBLISH.md update once #11 lands.

### 3.10 Verdict

**Recommendation**: Accept with reservations.

**Rationale**:

- AC #1, #2, #4 met; full smoke suite green (8 new cases); pre-flight verified manually on this branch (rejection with hint + bypass with WARNING).
- Pre-flight script + HOWTO + bypass are coherent deliverables — the user can publish today (with `PUBLISH_ALLOW_ANY_BRANCH=1` from this branch, or normally from `main` after merge).

**Reservations**:

1. AC #3 (user-driven `0.1.x` round) deferred — depends on user PyPI credential setup and is logically downstream of #11. Captured as TODO follow-up.
2. HOWTO-PUBLISH.md needs a small update once #11 lands to recommend `publish-quality` as the safe entry. Captured as TODO follow-up.

## Governance trace

| Source                                 | Clause                 | Action  | Note                                                                |
| -------------------------------------- | ---------------------- | ------- | ------------------------------------------------------------------- |
| CEREMONIES.md `Task start`             | Task start ceremony    | applied | TODO #1 → GH #9 → branch + devlog with mandate gate                 |
| CLAUDE.md `Moderate auto mode`         | Stop-and-ask           | applied | proposed scope + TestPyPI question before creating issue            |
| CLAUDE.md `YAGNI`                      | YAGNI                  | applied | shell pre-flight, no Python helper; no TestPyPI; no CI              |
| CLAUDE.md `Confidence and attribution` | Verified facts         | applied | `uv publish --help` consulted re token storage                      |
| CLAUDE.md `Naming discipline`          | Outcome-named          | applied | `publish-preflight`, `PUBLISH_ALLOW_ANY_BRANCH`                     |
| CEREMONIES.md `Convergence check`      | Reaching vs retreating | applied | bypass added in one mid-task round, not iterated to death           |
| CLAUDE.md `Convergence check`          | Stop and surface       | applied | #9 ↔ #11 reciprocal dependency surfaced + user chose merge order    |
| MEMORY.md `Blocked edit workaround`    | Use Write tool         | applied | § 3 closure fill used Write (Edit hook-blocked by user attestation) |
| CEREMONIES.md `Task closure`           | Task closure ceremony  | applied | this section                                                        |

## Resource consumption

| Phase          | Tokens (approx) | Wall time  |
| -------------- | --------------- | ---------- |
| Mandate + plan | ~25k            | 30 min     |
| Implementation | ~80k            | 1 h        |
| Bypass + tests | ~30k            | 30 min     |
| Closure        | ~30k            | 30 min     |
| **Total**      | **~165k**       | **~2.5 h** |

| Counter                | Value                                                                                                       |
| ---------------------- | ----------------------------------------------------------------------------------------------------------- |
| Pre-commit hook fails  | 1 (Edit hook on § 3 fill — used Write tool per documented workaround)                                       |
| Subagent invocations   | 0                                                                                                           |
| `/clear` events        | 1 (at task start)                                                                                           |
| Memory rotation events | 0                                                                                                           |
| LOC changed            | +393 / -1 (`git diff main...HEAD --stat`)                                                                   |
| Files changed          | 5 (Makefile, scripts/publish-preflight.sh, HOWTO-PUBLISH.md, tests/smoke/test_publish_preflight.py, devlog) |
| Commits on branch      | 5                                                                                                           |
