# 0017 — Tune zero-count badge colour

- GH issue: #17
- Branch: `impl/0017-zero-count-badge-colour`
- Opened: 2026-05-07
- Closed: 2026-05-07

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.7
- Review: user

### 1.1 Context

Execution, fast-path. Uncommitted v1.0.4 stub + `FG_GREY` tweak (`\x1b[90m` → `\x1b[37m`) on `main` moved to this branch on task start.

### 1.2 Problem statement

Zero-count badge renders as `BG_BLACK + FG_GREY + text` (`_cli.py:36`). With `FG_GREY = \x1b[90m`, terminals whose "bright black" sits too close to true black render the badge unreadable.

### 1.3 Goal

Pick an ANSI foreground that reads as muted-but-legible on `BG_BLACK` across the user's common terminals.

### 1.4 Design decisions

- Stay in base-16 ANSI; tune the existing `Ansi.FG_GREY` value, no new symbol.
- One muted colour for all zero-count states.

### 1.5 Test plan

Visual check on the user's terminal (default + dark theme); `make check` green.

### 1.6 Acceptance criteria

1. Zero-count badges visibly de-emphasised vs non-zero, but legible.
2. Non-zero badges (BUSY / ASKING / IDLE) unchanged.
3. `make check` green; `CHANGES.md` v1.0.4 entry written.

### 1.7 Coverage check

Within charter scope.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.7
- Review: user

### 2.1 Steps

1. Iterate on `Ansi.FG_GREY` value visually; lock the final code.
2. Update `CHANGES.md` v1.0.4 entry.
3. `make format && make check`; commit; push; PR `Closes #17`.

## 3. Closure

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

### 3.1 Implementation deviations

- Plan § 2.1 step 1 anticipated iteration on the `Ansi.FG_GREY` value. The first candidate (`\x1b[37m`) held across all five terminal/mode combinations tested (§ 3.7); no iteration occurred.
- `make check` first failed on `tests/smoke/test_version_matches_changes.py`: `__version__` resolved to `1.0.3` (cached editable wheel) while `CHANGES.md` topmost was `1.0.4`. `uv sync --extra dev` does not rebuild the editable wheel when `CHANGES.md` changes, even though `[tool.hatch.version]` derives the version from it. Resolved with `uv sync --reinstall-package claude-busy-monitor --extra dev`. Recorded as a factoring candidate.

### 3.2 File inventory

- modified: `src/claude_busy_monitor/_cli.py` — `Ansi.FG_GREY` `\x1b[90m` → `\x1b[37m`.
- modified: `CHANGES.md` — v1.0.4 entry.
- new: `architecture/devlog/0017-zero-count-badge-colour.md` — this devlog.

### 3.3 Verification commands

```bash
make check                                                          # 28 unit + 14 smoke green
uv sync --reinstall-package claude-busy-monitor --extra dev         # refresh __version__ post-CHANGES.md bump
claude-busy-monitor                                                 # visual: zero-count badges legible-muted
```

### 3.4 Coverage check

Within charter scope.

### 3.5 Test review

- _Coverage_: no automated test added. Colour rendering is visual; an ANSI-string assertion would lock the value without testing readability — the actual failure mode the task addresses.
- _Effectiveness_: `tests/smoke/test_version_matches_changes.py` bit during closure — caught the editable-wheel / CHANGES.md drift before commit. Test paid off.

### 3.6 Gate check

- AC #1: ✓ — verified across 5 terminal/mode combinations (§ 3.7).
- AC #2: ✓ — `_STATE_STYLE` (`_cli.py:29`) for BUSY/ASKING/IDLE untouched.
- AC #3: ✓ — `make check` green; `CHANGES.md` v1.0.4 entry present.
- Mandate § 1 + § 2 user-attested before code change committed (commit `5ad70dc`).

### 3.7 Manual validation

Zero-count badge rendering (`Ansi.FG_GREY = \x1b[37m`) verified by user on:

- MATE Terminal — light and dark modes
- Terminator — light and dark modes
- xterm — dark mode

Legible-muted on all combinations tested; no failure mode reproduced. xterm light mode not tested — known gap.

### 3.8 Retrospective

| #   | Point                                                                                                                                                           | Agent    | User          |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------- |
| 1   | Fast-path was the right shape — mechanical scope, no design ambiguity, single-pass execution                                                                    | well     | _(pending)_   |
| 2   | First colour candidate (`\x1b[37m`) held across 5 terminal/mode combinations; no iteration despite plan anticipating it                                         | well     | _(pending)_   |
| 3   | `make check` failed once on `test_version_matches_changes` — editable-wheel stale-vs-CHANGES.md drift; resolved with `--reinstall-package` (factoring candidate) | not well | _(pending)_   |

### 3.9 Verdict

**Recommendation**: Accept.

**Rationale**:

- All ACs met (#1, #2, #3); five terminal/mode combinations validate the readability claim.
- `make check` green (28 unit + 14 smoke).
- Single-line code change, no API surface change, no scope creep.

## Governance trace

| Source                                            | Clause                | Action  | Note                                                                         |
| ------------------------------------------------- | --------------------- | ------- | ---------------------------------------------------------------------------- |
| CEREMONIES.md `Fast-path task flow`               | Eligibility check     | applied | mechanical, scope ≤ paragraph, no design decisions                           |
| CLAUDE.md `No task-related commits on main`       | Branch hygiene        | applied | uncommitted FG_GREY tweak + v1.0.4 stub stashed and moved to task branch    |
| CLAUDE.md `Naming discipline`                     | Outcome-named         | applied | branch / devlog name describe the WHAT (which badges, what aspect)           |
| CLAUDE.md `EN_UK for prose`                       | Spelling              | applied | "colour" throughout devlog, CHANGES.md entry, branch name                    |
| CLAUDE.md `Lean mandate + execution plan`         | Compression           | applied | § 1 + § 2 compressed to ~14 body lines (~60% of free draft)                  |
| CLAUDE.md `YAGNI`                                 | Scope discipline      | applied | no terminal-capability detection, no new ANSI symbol, no per-state variant   |
| MEMORY.md `Run make format after every code edit` | Formatter clean       | applied | `make format` run before commit                                              |
| CLAUDE.md `Review-attestation hook workaround`    | Edit-span widening    | applied | § 3.1 (Manual validation, pre-renumber) added by widening Edit span          |
| CEREMONIES.md `Task closure`                      | Task closure ceremony | applied | this section                                                                 |

## Resource consumption

| Phase                          | Tokens (approx) | Wall time   |
| ------------------------------ | --------------- | ----------- |
| Task start (issue, branch)     | ~10k            | 5 min       |
| Mandate + plan + compression   | ~15k            | 15 min      |
| Code work + CHANGES wording    | ~10k            | 10 min      |
| Manual validation (user-side)  | (n/a)           | ~10 min     |
| Closure                        | ~25k            | 20 min      |
| **Total**                      | **~60k**        | **~60 min** |

| Counter                | Value                                                            |
| ---------------------- | ---------------------------------------------------------------- |
| Pre-commit hook fails  | 0                                                                |
| Subagent invocations   | 0                                                                |
| `/clear` events        | 0                                                                |
| Memory rotation events | 0                                                                |
| LOC changed            | +76 / -1 (`git diff main...HEAD --stat`, pre-closure)            |
| Files changed          | 3 (`_cli.py`, `CHANGES.md`, devlog 0017)                         |
| Commits on branch      | 2 pre-closure (mandate + code/CHANGES); +1 anticipated (closure) |

## Factoring candidates

- `Makefile:test-smoke` / `Makefile:check` — `uv sync --extra dev` does not rebuild the editable wheel when `CHANGES.md` changes, so `__version__` (resolved via `[tool.hatch.version]` regex over `CHANGES.md`) goes stale and `test_version_matches_topmost_changes_heading` fails until manual `--reinstall-package`. Candidate fix: prepend `uv sync --reinstall-package claude-busy-monitor --extra dev` (or `make install` semantics) when `CHANGES.md` is newer than the installed wheel metadata. Hit count: 1 (#17).
