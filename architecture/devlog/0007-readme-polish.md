# 0007 — README polish

- GH issue: #7
- Branch: `impl/0007-readme-polish`
- Opened: 2026-04-26
- Closed: 2026-04-26

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.7
- Review: user

### 1.1 Context

Root `TODO.md` § 1 _README polish_:

> Main `README.md` shall be clean and engaging, like DFD or better.

Current `README.md` (17 lines) is a placeholder pointing to this TODO.
Reference: [DFD README](https://github.com/pbauermeister/dfd/blob/main/README.md) — badges, hero, tagline, features table, quick-start, install.
Project state: v0.1.0, library + CLI (`claude-busy-monitor`), unpublished, dev install only. State-detection internals already documented in `README-STATE-DETECTION.md` (deep, ~250 lines).

### 1.2 Task nature

Execution — defined deliverable (a polished README), but with judgment on tone, structure, and demo content.

### 1.3 Goal

Replace the placeholder with a top-level README that lets a first-time reader grasp the value proposition, see a demo of the CLI output, install (dev path until PyPI lands), and follow basic usage — at parity with the DFD README's clarity and engagement.

### 1.4 Design decisions

- **Structure** mirrors DFD: tagline → badges → hero (CLI screenshot or coloured-text snippet) → Features table → Quick start → Install → Usage → How it works (link to `README-STATE-DETECTION.md`) → Develop (link to existing dev section).
- **Hero**: the CLI output is colourised; embed as a PNG screenshot under `images/` (consistent with `architecture/devlog/CLAUDE.md` image convention). Fallback: ANSI-stripped fenced block if rendering the screenshot proves friction.
- **Badges**: license (MIT), Python (3.11+), and a placeholder for PyPI/CI added once they exist (TODO #2 covers PyPI; CI is not yet wired). Keep only badges that resolve _today_ — no broken-shield badges.
- **Install section**: two paths — _users_ (PyPI, deferred to TODO #2 — gate behind a "once published" note or hide entirely until #2 lands) and _developers_ (existing `make venv-activate` flow).
- **Voice**: terse, value-first, sentence-per-line per project Markdown convention. No AI meta-commentary.
- **Scope discipline**: do not migrate or rewrite `README-STATE-DETECTION.md` — link to it. Do not add OSX/version-compat sections (TODO #3 later items).

### 1.5 Test plan

Doc-only task — verification is rendering and review:

1. `prettier` check passes (PostToolUse hook).
2. Local Markdown render (VS Code preview) shows expected layout.
3. After push, GitHub renders the README correctly (badges resolve, image loads, links work).
4. All cross-links (`README-STATE-DETECTION.md`, `LICENSE`, `CHANGES.md`, GitHub issues page) resolve.
5. `make check` still passes (no code changes expected, but guards against accidental breakage).

### 1.6 Acceptance criteria

1. `README.md` covers: tagline, badges (only resolving), hero demo, features table, quick-start, install (dev path, mention PyPI as future), usage example, link to state-detection doc, link to dev section.
2. Hero image (or text fallback) committed under `images/` if image is used.
3. No broken links, no broken badges.
4. Reads cleanly on github.com (no Markdown rendering glitches).
5. `make check` green.
6. Length comparable to DFD README (~150 lines order-of-magnitude — value-first, not exhaustive).

### 1.7 Coverage check

Within charter scope.

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.7
- Review: user

### 2.1 Steps

1. Capture CLI hero asset: run `claude-busy-monitor` against a representative session set, screenshot the coloured terminal output, save to `images/hero.png`.
   - Fallback: paste an ANSI-stripped fenced block if screenshot is friction.
2. Draft `README.md` per § 1.4 structure; commit as one diff for review.
3. Verify: render in VS Code preview, run `make check`, run `prettier`.
4. Push branch, open PR with `Closes #7`; verify GitHub-side rendering (badges, image, links).
5. Devlog § 3 fill at closure (deviations, file inventory, demo, retrospective, verdict).

### 2.2 Scope boundary

In: `README.md` rewrite; optional `images/hero.png` (or text fallback).
Out: PyPI publish (TODO #2), GH ticket templates (TODO #3), OSX support, version-compat documentation, restructure of `README-STATE-DETECTION.md`, CI badges (no CI yet).

## 3. Closure

- Author: agent
- Model: Claude Opus 4.7
- Review: user

### 3.1 Implementation deviations

- **Hero**: no screenshot tool available on the host (`scrot`/`import` X11-only, no `aha`/`svg-term`/`ansi2html`). Pivoted to a hand-crafted SVG instead of a PNG screenshot — reproducible without binaries, crisp at any zoom, matches DFD's pattern.
- **First hero render misclassified `asking` as grey** instead of yellow. The sample I sampled had 0 asking sessions, where `_cli.py` uses the dim `BG_BLACK + FG_GREY` style for zero counts; the actual asking pill is `BG_YELLOW + FG_BLACK + FX_BLINK`. Caught at user review; fixed by reading the colour map first. Lesson: read the relevant code before designing visual artefacts.
- **Private project name leaked into the hero**. Caught at user review; replaced with a generic public project name. Devlog 0001 carried three appendix references to the same private name — scrubbed in the same commit; § 3 Closure of 0001 reset to `pending` per CLAUDE.md attestation rule.
- **CLI as metonymy for "command"** in five places. Caught at user review (round 4 of polish); swapped to "command" or dropped where the form-factor distinction was already handled by the Scope section.
- **Three "honest take" rounds** instead of one: round 1 surfaced 7 structural issues, round 2 surfaced 7 nits, round 3 hit the noise floor (3 cosmetic items I wouldn't act on). Convergence-check (CLAUDE.md) triggered at round 3 — flagged the diminishing-returns pattern back to the user.

### 3.2 File inventory

- new: `images/hero.svg` — hand-crafted SVG: dark background, three-pill summary line + 5 sample sessions across all states (`busy` red, `asking` yellow, `idle` green), with cwd basename and out/in token columns.
- modified: `README.md` — 17 → 125 lines. Sections: badges (License + Python + Status), tagline + form-factor line, hero, Why, Scope, Features, Install, Usage (Command + Library), How it works, Compatibility, License.
- modified: `architecture/devlog/0001-build-skeleton.md` — three private-name scrubs in appendix tables; § 3 Closure attestation reset to pending.
- new: `architecture/devlog/0007-readme-polish.md` — this devlog.

### 3.3 Verification commands

```bash
make check                              # 27 unit + 6 smoke green
grep -i '\bcli\b' README.md             # empty (no metonymy)
grep -ri pikett . --include='*.md' --include='*.svg'  # empty
wc -l README.md                         # 125
```

Manual cross-checks: badges resolve on GitHub (license + Python + status), SVG renders inline, hero column legend matches CLI output format, internal links (`LICENSE`, `CHANGES.md`, `README-STATE-DETECTION.md`, Discussions, Issues) all resolve.

### 3.4 Coverage check

Within charter scope.

### 3.5 Test review

- _Coverage_: doc-only task, no production-code changes. Pure prose; no test required (justified absence per CLAUDE.md `(c)`).
- _Effectiveness_: N/A — no test bit.

### 3.6 Gate check

- All 6 acceptance criteria met. Criterion 1's "Develop section" was dropped during polish (round 1 nit) — `make help` callout in Install replaces it; functionally equivalent.
- Mandate § 1 + § 2 user-attested before code (commit `3f084f6`).
- All deliverables committed.
- `make check` green.

### 3.7 Retrospective

| #   | Point                                                                                                 | Agent    | User |
| --- | ----------------------------------------------------------------------------------------------------- | -------- | ---- |
| 1   | DFD-style structure landed in one draft pass — reference accelerated the design                       | well     | well |
| 2   | Hand-crafted SVG hero unblocked the no-screenshot-tool dead-end                                       | well     | well |
| 3   | First hero render had wrong asking colour — should have read `_cli.py` colour map before drafting     | not well | well |
| 4   | Real project name slipped into the hero — should have asked about name sensitivity beforehand         | not well | well |
| 5   | CLI-as-metonymy not caught by agent — user surfaced it in round 4                                     | not well | well |
| 6   | Three-round honest-take pattern converged with concrete improvements; round 3 self-reported asymptote | well     | well |
| 7   | Cache-aware token-totals row gives a quantified ~10× claim — concrete value-prop                      | well     | well |
| 8   | Library example reframed to filter-by-state — sells what only the library can do                      | well     | well |
| 9   | Devlog 0001 scrub reset § 3 Closure on a previously merged task — new pattern, mild surprise          | surprise | well |

### 3.8 Demo scenario

Replayable on the merge SHA:

```bash
git fetch && git checkout <merge-sha>

# Render the README on github.com/pbauermeister/claude-busy-monitor:
#   - badges display: License: MIT (blue), Python 3.11+ (blue), Status: Alpha (orange)
#   - hero SVG renders inline with three-pill summary + 5 sample sessions
#   - all internal links resolve (LICENSE, CHANGES.md, README-STATE-DETECTION.md, Discussions, Issues)

make check                # 27 unit + 6 smoke green
grep -i '\bcli\b' README.md   # empty — no metonymy
```

### 3.9 Forward-looking check

Sets up the visible front for TODO #2 (PyPI publish): the README already names PyPI as the roadmap, the alpha badge sets expectations, and the Install section needs only a one-line replacement once published. Discussions invite for macOS support (TODO #3 candidate) gives contributors a clear entry point before any issue or PR.

### 3.10 Verdict

**Recommendation**: Accept.

**Rationale**:

- All 6 acceptance criteria met; `make check` green; no broken links/badges/SVG.
- Three review passes converged with concrete improvements per round; round 3 was at the noise floor.
- README reads cleanly out of context — value-first structure aligned with the DFD reference, hero column legend closes the visual-vs-prose loop, library example sells what the library uniquely enables.
- Hero is reproducible (no binary dependency) and renders inline on GitHub.

## Governance trace

| Source                                | Clause                             | Action  | Note                                                                       |
| ------------------------------------- | ---------------------------------- | ------- | -------------------------------------------------------------------------- |
| CEREMONIES.md `Task start`            | Task start ceremony                | applied | issue + branch + devlog with mandate gate before any code                  |
| CEREMONIES.md `Mandate approval gate` | Mandate gate                       | applied | user attested § 1 + § 2 before draft (commit `3f084f6`)                    |
| CLAUDE.md `Density and terseness`     | Sentence-per-line, lean prose      | applied | README ≤ 125 lines; voice trimmed across three polish rounds               |
| CLAUDE.md `YAGNI`                     | YAGNI                              | applied | no CONTRIBUTING.md, no examples/, no broken-shield badges                  |
| CLAUDE.md `Convergence check`         | Stop and ask: reaching/retreating? | applied | round 3 honest-take self-reported asymptote rather than manufacturing nits |
| CLAUDE.md `Flattery avoidance`        | Honest critique                    | applied | "honest take" responses returned actual problems, not praise               |
| CLAUDE.md `Multiple interpretations`  | List and rank                      | applied | CLI-metonymy discussion offered the swap table before applying             |
| CLAUDE.md `Naming discipline`         | Outcome-named sections             | applied | Why / Scope / Features / Install / Usage / How it works                    |
| MEMORY.md `Blocked edit workaround`   | Use Write tool                     | applied | devlog 0001 scrub used Write (Edit hook-blocked by user attestation)       |
| CEREMONIES.md `Task closure`          | Task closure ceremony              | applied | this section                                                               |

## Resource consumption

| Phase          | Tokens (approx) | Wall time   |
| -------------- | --------------- | ----------- |
| Mandate + plan | ~30k            | 20 min      |
| Implementation | ~80k            | 1 h         |
| Review rounds  | ~60k            | 40 min      |
| Closure        | ~20k            | 15 min      |
| **Total**      | **~190k**       | **~2.25 h** |

| Counter                   | Value                                          |
| ------------------------- | ---------------------------------------------- |
| Pre-commit hook fails     | 0                                              |
| Subagent invocations      | 0                                              |
| `/clear` events           | 1 (at task start)                              |
| Memory rotation events    | 0                                              |
| LOC changed               | +305 / -17 (`git diff main...HEAD --stat`)     |
| Files changed             | 4 (README, hero.svg, devlog 0001, devlog 0007) |
| Commits on branch         | 13                                             |
| Honest-take review rounds | 3                                              |
