# Devlog conventions

- Store images in `images/` (relative to this directory), not alongside the Markdown files.

## Standard structure

Devlogs have three top-level sections, each carrying its own review metadata. The file has no file-level metadata block.

```markdown
# NNNN — Short title

- GH issue: #NNN
- Branch: `<category>/NNNN-short-description`
- Opened: YYYY-MM-DD
- Closed: YYYY-MM-DD

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.7
- Review: user [reviewed before implementation starts]

### 1.1 Context

### 1.2 Task nature

### 1.3 Problem statement

### 1.4 Goal

### 1.5 Design decisions

### 1.6 Test plan / fixtures

### 1.7 Acceptance criteria

### 1.8 Watchlist reminder

### 1.9 Coverage check

## 2. Execution plan

- Author: agent
- Model: Claude Opus 4.7
- Review: user [reviewed before implementation starts]

### 2.1 Steps

### 2.2 Scope boundary

## 3. Closure

- Author: agent | user+agent
- Model: Claude Opus 4.7
- Review: user [reviewed at task closure]

### 3.1 Implementation deviations

### 3.2 File inventory

### 3.3 Verification commands

### 3.4 Coverage check

### 3.5 Test review

### 3.6 Gate check

### 3.7 Manual validation

### 3.8 Demo scenario

### 3.9 Retrospective

### 3.10 Forward-looking check

### 3.11 Verdict

## Governance trace

## Resource consumption

## Factoring candidates
```

### Rules

- **Three review gates**: § 1 Mandate, § 2 Execution plan, § 3 Closure each carry their own `- Author: / - Review:` block.
- **Model field**: when `Author` includes `agent`, add `- Model: <name + version>` (e.g. `Claude Opus 4.7`). Omit when `Author` is `user` only.
- **No file-level metadata block**. The top-section attestations replace the legacy file-level one.
- **Subsections inherit** their parent top-section's metadata. Do not repeat `- Author:` / `- Review:` on subsections.
- **Reset granularity is the top section**: an agent edit inside § 1.x resets § 1's review to `pending`; an edit inside § 2.x resets § 2's review; an edit inside § 3.x resets § 3's review. Other top sections are unaffected.
- **Review timing**:
  - § 1 Mandate and § 2 Execution plan are reviewed at task start, before any implementation begins.
  - § 3 Closure is reviewed at task closure, covering implementation deviations, outcomes, retrospective, etc.
- **Optional subsections**: any `### x.y` can be dropped if not applicable to the task — prefer omission over `(n/a)` placeholders.
- **Subsection numbering is local and continuous**: when an optional subsection is omitted, renumber the remaining subsections so each `### N.x` sequence within § 1, § 2, § 3 is gap-free. The subsection _title_ is the stable identifier (e.g. "Design decisions" always means the same thing across devlogs); the _number_ is local to each devlog. Cross-devlog references must cite both (e.g. `§ 1.3 Design decisions (#162)`), not the number alone. Originating incident: #174 shipped with gaps at § 1.3, 1.6, 1.8, 3.3, 3.7, 3.8; #174 is not retro-fixed but future devlogs follow this rule.
- **`## Governance trace` and `## Resource consumption`** are appendices, not numbered sections, and carry no review metadata (the content is factual and covered by § 3 Closure's attestation).
- **§ 3.5 Test review records two things**:
  - _Coverage_ — did the task's code changes get test support? For each change or refactor, decide: (a) covered by an existing test — note which; (b) add a new test that also exercises the pre-change code (so it would have caught the original failure mode); (c) justify absence (pure prose change, one-off script).
  - _Effectiveness_ — did any test bite during the task, i.e. catch a real error that would otherwise have slipped? Record the test name and the error it caught. Anecdote now, data later.
- **No planned File inventory in § 2**. The file inventory lives in § 3.2 only (effective, at closure). § 2.1 Steps may name files inline when describing a step; that is not a separate subsection and does not count as a planned inventory. If the effective § 3.2 set diverges from § 2.1's inline mentions, note the divergence briefly in § 3.2.
- **Lean devlog**: compress prose to ~150 lines at closure. Drop `_(filled at closure)_` placeholders for subsections that were not used. Keep metadata blocks, governance trace, retrospective voting table, and resource consumption table untouched — those carry analysable structure that tooling and future agents depend on.
- **Lean mandate + execution plan**: produce § 1 Mandate + § 2 Execution plan in two passes, same response — free draft (whatever length the task naturally calls for), then compressed version at ~60% of the free-draft body-line count. Only the compressed version persists in the file. Exploratory tasks (§ 1.2 Task nature = _Exploratory_) may skip the compression pass — mandates are deliberately broad (#32 WP-2.1 lesson). The ~150-line closure budget still applies file-wide; this rule governs pre-implementation state.

  Compression direction — cut first, ranked:
  1. Established rationale (reasoning already in `CLAUDE.md`, tool docs, Makefile, or input docs — cite by path, don't restate).
  2. Paragraph prose where a bullet suffices.
  3. Restated rules from input documents.
  4. Defensive justification of obvious choices — keep only for non-obvious choices or reversals of prior convention.
  5. Overlapping subsections: § 1.3 Problem statement ↔ § 1.1 Context when redundant; § 1.5 Test plan ↔ § 1.6 Acceptance when restating; § 1.7 Watchlist / § 1.8 Coverage check compress to one line each when nothing special applies.

  Form rules for what stays:
  - Terse bullets — each ≤ 2 lines; longer means several bullets.
  - Steps as one-liners; nested sub-bullets are a signal to split the step or cite the file where detail lives.
  - Sentence-per-line for remaining prose (project Markdown convention).

  **Revision preservation**: post-compression discussion modifies existing prose; does not append — maintain the compression ratio through iteration.

- **§ 3.11 Verdict**: agent self-assessment recommendation to the reviewer, one of _Accept_, _Reject_, or _Accept with reservations_. Structure: a bold one-line **Recommendation**; a **Rationale** bullet list (positive evidence — acceptance criteria met, tests green, design properties achieved); and, for _Accept with reservations_, a **Reservations** numbered list naming each deferred or missing item and why it does not block merge (for _Reject_, list what must change before re-submission instead). The verdict is self-assessment, not a decision — the reviewer retains the call. Purpose: surface known gaps and deferred follow-ups in one place rather than leaving the reviewer to infer them from § 3.1 / § 3.5 / § 3.10. Reservations that graduate to persistent follow-ups must also be captured in `TODO.md` so they survive devlog closure.
- **`## Factoring candidates` appendix (optional)**: free-text one-liners for duplication, recurring parameters, or parallel shapes noticed during the task (not actively researched). Format: `- <file:line or pattern name> — <short description>`. Omit the whole section if no candidates. Input for the periodic _Factoring review_ ceremony (governance task pending); the appendix accumulates candidates cross-task regardless of whether the ceremony runs today.
