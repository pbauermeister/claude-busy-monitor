# Agent Instructions

<!-- ------------------------------------------------------------
BLOCK 1: PROJECT CONVENTIONS (manual — user may edit directly)
------------------------------------------------------------- -->

## Project structure

- `architecture/ARCHITECTURE.md` — Living implementation architecture reference
- `architecture/input/` — Architecture input documents (analysis, design, Phase 0 architecture)
- `product/` — Product requirements, decisions, domain inputs
- `governance/` — AI-augmented engineering charter and governance
- `studies/` — Research and analysis scripts (standalone, not maintained with the platform)
- `*/devlog/` — Task devlogs (each top-level folder has its own)

## Key documents

None yet.

## Document toolchain

- Markdown with PlantUML and DFD diagrams; PDFs via `pandoc`
- Diagram edge colours carry no meaning; invisible edges are layout-only constraints

## Document lifecycle

- Living documents have a maintained document history section
- When outcomes are published externally (e.g. PDFs shared or copied), a git tag is applied
- Major versions of living documents: allocate a git tag and note it in the document history
- External-facing documents: no AI authoring attribution or editorial artefacts — authorship defaults to user
- Review status may be mentioned in external documents
- AI collaboration is not a secret; deliberate exceptions are allowed
- When agent contributes to a document with a history table, the history entry includes the agent model identifier (e.g. "Claude Opus 4.6")
- **Living documents** (topic-scoped): update content in-place where it belongs; add `[Update]` annotation if the change is notable, plus a line in the document history
- **Devlogs, discussions, outcomes** (task-scoped): append-oriented — mandate first, then outcomes accumulate; post-closure changes get `[Updated DATE: summary]` annotations

## GitHub tickets and PRs

- Prefix every issue and PR title with a category tag: `[gov]` governance, `[arch]` architecture, `[impl]` implementation, `[study]` studies

## Devlog and issue tracking

- Every task has a devlog entry (`<folder>/devlog/NNNN-*.md`), a GitHub issue, and a git branch (created at task start per `CEREMONIES.md`)
- Branch naming: `<category>/NNNN-short-description` — e.g. `impl/0102-grafana-sql-validator`, `gov/0104-governance-traceability`, `study/0100-validate-grafana-sql`
- No task-related commits on `main`; work happens on the task branch
- Housekeeping changes (TODO.md, Makefile, governance files) are committed on `main` directly — avoids mixed commits that can't be cherry-picked
- `TODO.md` is the capture buffer for ideas arising during work — low friction (one line), scannable (non-duplication at a glance), historised in git. Items either graduate to GH issues (when tackled) or get discarded. GH issues are for execution tracking, not for brainstorming.
- Devlog filename: `NNNN-short-description.md` (four-digit zero-padded GH issue number)
- Outcome documents: `NNNN-short-description--outcome-topic.md` (alongside the devlog)
- Discussion documents: `NNNN-short-description-discussion.md` (and `-discussion-2.md` etc.)
- Issue numbers are shared across architecture and implementation
- Devlog folder: `[arch]` and `[impl]` tasks use `architecture/devlog/`; `[gov]` tasks use `governance/devlog/`; `[study]` tasks use `studies/devlog/`
- Devlog mandates include a `### Context` field listing predecessor tasks that provide essential context
- Architecture document history entries reference the motivating task/issue number
- New conventions must be codified in project files (CLAUDE.md, CEREMONIES.md, or implementation/CLAUDE.md), not only in agent memory. Memory is per-instance; project files are authoritative across all sessions.
- Devlog review granularity (supersedes Block 3 granularity for devlogs):
  - **Top-section level only**: § 1 Mandate, § 2 Execution plan, § 3 Closure each carry their own `- Author: / - Review:` block. No file-level metadata block, no per-subsection metadata. See `architecture/devlog/CLAUDE.md` for the full standard structure.
  - **Three review gates**:
    - § 1 Mandate and § 2 Execution plan are reviewed before implementation starts.
    - § 3 Closure is reviewed at task closure.
  - **Subsections inherit their top-section's metadata**. An agent edit inside § N.x resets § N's review to pending; other top sections are unaffected.
  - **Review reset is tool-agnostic**: any agent modification to user-reviewed content — whether via the Edit tool, sed, Bash, or any other mechanism — requires resetting the relevant top-section review to pending.
    Using an alternative editing mechanism does not exempt from this rule.
  - **In-file attestation is the only accepted review**: before passing any review gate, the agent must verify that the top section carries user review attestation _in the file_.
    Verbal confirmation in the conversation ("reviewed", "Go") is not a substitute.
    The agent must not begin implementation until both § 1 Mandate and § 2 Execution plan carry user review attestation in the file.

## Permissions

- Changes to `CLAUDE.md`, `CEREMONIES.md`, and `.claude/settings.json` require user review before commit — no exceptions
- Always allowed to run read-only filesystem commands and git read commands without asking
- Always allowed to modify files in this project or in /tmp/ without asking
- Agent must confirm with user before force-pushing, even when a requested squash implies it
- PR merge is user's action: agent pushes, user merges — do not run `gh pr merge` unless user explicitly says "merge it" or equivalent
- **Default for pushed branches: leave history untouched.** Don't rebase and don't pull main's new commits into the task branch. Housekeeping commits on main (TODO.md, MEMORY.md, etc.) almost never need to reach the task branch; final squash-merge at PR time handles integration. The reflex to "keep rebased on latest main" is the root of most force-push friction.
- **Exception**: if the branch genuinely needs main's new commits (merge conflict, compile error), `git merge main` onto the task branch — **ask the user first** before running.
- **`git fetch` before acting on a pushed branch.** `git status` then reports "behind origin by N commits" if origin has moved — a silent prerequisite for every branch-state decision.

## Task execution

- When executing multiple steps, assess whether each is small (mechanical) or massive (architectural, multi-file) — if massive, offer to pause and debrief after each step
- **Fast-path task flow.** Mechanical tasks whose scope is already captured in a pre-existing artefact (TODO item, ceremony definition, or explicit user brief) may use the lightweight flow in `CEREMONIES.md` § Fast-path task flow: single-pass devlog at closure, all three attestations applied together, all audit artefacts preserved. Standard flow remains the default for design, architectural, or cross-cutting work.
- **Moderate auto mode during discussions.** Auto mode is a _tool-friction_ lever (fewer "allow this command" prompts for unattended execution), not a _discussion-friction_ lever. When the user asks for the agent's take, opinion, or proposal ("Your take?", "Propose...", "Agree?", "What do you think?", or equivalent), the agent gives the opinion and stops — no branch, edit, commit, or scaffold. Action requires an explicit go-ahead ("proceed", "apply", "do it", "yes", or equivalent). Default to stop-and-ask when ambiguous.
- **Convergence check**: if a task goes through 3+ revision rounds and each round _narrows scope_ (dropping layers, walking back prior decisions) rather than adding substance, either party (user or agent) must stop and ask: are we reaching, or retreating? Cost of asking is one turn; cost of continuing is compounded. Three circuit-breakers in one task is too many. Originating evidence: #148 ran five rounds of post-PR refinement before a structural reframe; each round shrank the design (two layers → one layer → agent directive → hook → `$CLAUDE_ENV_FILE`).
- **Code-reuse: frameworks and libraries.** During § 2 Execution plan drafting — when implementation details are being worked out — consider whether an existing framework or library solves the problem. Frameworks and libraries provide battery-powered, battle-tested solutions for problems where domains/layers interact, abstracting implementation details from use-case parameters. Trigger signals: (a) substantial new code volume (rough ≥100 hand-written production LOC, or a new module/abstraction), OR (b) problem domain with a known solved space (parsing, date/time, HTTP, crypto, retry, scheduling, etc. — regardless of LOC). Stop and surface to the user if a framework or library is a candidate. Reuse-triggered plan rewrites are correct outcomes — responsible redesign on new information — distinct from the convergence-check's scope-narrowing-without-progress pattern. Code accumulates faster than the user can maintain — unreviewed new code is debt. All code must be human-maintainable: readable out of context, outcome-named (per § Naming discipline), commented only for non-obvious WHY. (Factoring — detecting duplication / recurring patterns in existing code — is a distinct concern handled by a periodic ceremony, not this per-task trigger; devlog captures any factoring candidates noticed during a task in the `## Factoring candidates` appendix.)
- **Script language (shell vs Python).** Default to Python. Stay in shell only for (a) very short process/filesystem commands, (b) pure command processors, (c) stream juggling / redirects. Options or arguments → Python (`argparse`). String manipulation, data structures, nesting, or typing → Python. In doubt, debate with the user. See `HOWTO-SCRIPTS.md` for signals, caveats, and lived examples.

## Language

- EN_US for code (including identifiers, symbols, and comments)
- EN_UK for prose (documentation, devlogs, commit messages)
- Requirement-strength keywords in prose: use MUST / MUST NOT / SHOULD / SHOULD NOT / MAY per [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) when requirement strength matters. Applies to new prose in `.md` files (governance, architecture, HOWTO, devlog); existing lowercase `must`/`should` usage is not retrofitted. Code comments remain identifier-driven (see § Naming discipline), not keyword-qualified.

## Naming discipline

- Names describe _what_ (output/purpose), not _how_ (technology/discipline)
- Apply at each abstraction level: containers, modules, functions, variables, API endpoints

## YAGNI

- Apply YAGNI strictly — don't build what isn't needed yet
- Exception: a one-line preventive measure that avoids small but certain tech debt is justified (e.g. defaulting a config to a production-safe value)
- The test: "will someone later have to investigate why this behaves unexpectedly in a different environment?"

## Markdown formatting

- Prettier enforces table formatting, list markers, and spacing — run via PostToolUse hook on `.md` edits
- Config: `implementation/.prettierrc` (`proseWrap: preserve`)
- Use `_` (underscore) for italics and `**` for bold — compatible with Prettier defaults
- No column-based line wrapping; break paragraphs at sentence boundaries (one sentence per line)
- No consecutive blank lines
- File ends with a single newline
- No trailing whitespace
- Headings from level 2 and below are always numbered in documents
- Prefer numbered lists over bullets in documents reviewed or cross-referenced across devlogs / PRs / retros — stable item numbers allow precise citation (e.g. "§ 5.3 item 2"); keep bullets only for unordered attribute sets nobody would reference individually

## Density and terseness

Applies to both agent responses in chat and Markdown output in documents.

- **Response length proportional to question complexity**: informational questions → 1–3 sentences per idea; comparative questions → tables beat bullets beat prose
- **No preambles, no epilogues**: skip "let me…", "I'll…", "there are three options here"; skip trailing "in short" recaps and meta-commentary on the question itself
- **Repetition ban**: don't restate what the reader just read — if a code block, table, or diagram shows X, the surrounding prose doesn't re-narrate X
- **Documents**: one statement per line; paragraphs ≤ 3 lines; rationale clauses ≤ 2 sentences; pros/cons cells are noun phrases, not sentences
- **Governance-trace Notes**: noun-phrase fragments, not full sentences
- **Deep-dive guard**: before answering in > ~300 words on a question that could plausibly want a short answer, ask "quick answer or deep dive?"
- **Terse does not mean sparse**: keep concrete file paths, line numbers, commit SHAs, explicit names; cut qualifiers, hedges, and restatement

## Preferences

- Favour squashing commits before merge, and small-scoped PRs
- For research/exploratory tasks, research established methods before designing a solution — hand-crafted approaches are often inferior to well-studied standard methods

<!-- ------------------------------------------------------------
BLOCK 2: COMPILATION PROTOCOL (protected — do not overwrite)

User prompts:
  Recompile: "Recompile CLAUDE.md from the Charter."
  Force:     "Force-recompile CLAUDE.md from the Charter."
             (skips semantic check, always rewrites Block 3)
------------------------------------------------------------- -->

## Compilation protocol

This section is protected: do not overwrite during recompilation.
Block 1 must never be modified during recompilation.

For the full compilation protocol (when and how to recompile), see `AI-AUGMENTED-ENGINEERING-CHARTER.md` Appendix A.
Some Charter-mandated rules are also enforced by `.claude/settings.json` hooks — during recompilation, check hooks before duplicating enforcement in Block 3.

### Structure of this file

- **Block 1** (project conventions) — manual, edit directly
- **Block 2** (this section) — compilation protocol, protected
- **Block 3** (compiled rules) — auto-generated from Charter, each rule tagged with `[charter § 12.X]` for human traceability

<!-- ------------------------------------------------------------
BLOCK 3: COMPILED RULES FROM CHARTER (auto-generated by agent)
------------------------------------------------------------- -->

## Interaction protocol

### Task nature [charter § 12.2]

Identify the task nature (exploratory or execution) and communicate it when starting work.
When ambiguous, ask.

- **Execution**: defined deliverables, strict rules, extrapolation flagged and minimized
- **Exploratory**: open-ended, extrapolation allowed but marked `[extrapolation]`, scope warnings relaxed

### Task assessment [charter § 12.4]

- **Scope**: flag tasks too vague, broad, or monolithic.
  Suggest decomposition.
  Strongly enforced for execution; relaxed for exploratory.
- **Proportionality**: flag when solution is more complex than problem warrants.
  Ask: "What would we lose?"
- **Criticality**: assess before proceeding — can this be aggressively automated (low-risk, mechanical, reversible) or does it require strict human oversight (architectural, irreversible, domain-sensitive)?
- **Framing**: frame mandates by _desired outcome_, not by _mechanism_. "Ensure X" beats "detect and fix X-missing" — the former opens the door to structural answers; the latter anchors the design on validation mechanisms and hides the simpler option. Before drafting acceptance criteria, ask: can this be a structural invariant instead of a check? Originating evidence: #148 took five rounds of refinement before the framing flipped from "detect missing venv" to "ensure venv is always active"; the right primitive (`$CLAUDE_ENV_FILE`) was findable in round 1 under the right framing.

### Iterative workflow [charter § 12.7]

AI generates → human reviews → AI corrects → commit.
No step skips human review for non-trivial content.

## Confidence and attribution

### Fact/inference separation [charter § 12.3]

Distinguish facts, synthesis `[synthesis]`, and extrapolation `[extrapolation]`.
Mark non-grounded statements.

### Confidence levels [charter § 12.3]

Indicate confidence where it varies meaningfully across items.

### References [charter § 12.3]

When claims are based on external knowledge, provide sources.
Required for execution tasks; best-effort for exploratory.

### Flattery avoidance [charter § 12.3]

No praise or reinforcement lacking objective basis.
Positive assessments with factual justification are fine.

### Multiple interpretations [charter § 12.3]

When multiple interpretations are possible, list and rank them.

## Authorship and review

### Section metadata [charter § 12.1]

Every section in devlogs and charter documents carries:

```
- Author: user|agent|user+agent
- Model: <model name + version>   # only when Author includes `agent`
- Review: pending|agent|user|user+agent
```

Rules:

- Add `- Author: agent` to any section you generate substantially.
- When `Author` includes `agent`, add `- Model: <model name + version>` (e.g. `Claude Opus 4.7`) naming the agent's model.
  Update it whenever the authoring model changes.
  Omit for pure `user` authorship.
  Git commit trailers remain the historical record of prior models.
- Never set `- Review: user` — only the user may attest their own review.
- Never commit changes containing `- Review: user` attestations.
  If asked, refuse.
- Agent must commit all pending changes before the user affixes their review attestation. This ensures the attestation covers a committed state, not a moving target.
- Any agent edit to reviewed content resets the review to `- Review: pending` — no exceptions, regardless of whether the edit was self-initiated or user-requested, and regardless of whether the edited section is shared (e.g. voting table) or not.
  Granularity: an edit to the mandate section resets the mandate-level review; an edit elsewhere resets the file-level review.
  **Commit checkpoint:** before committing changes to a file carrying `- Review: user`, verify the attestation has been reset to `- Review: pending`. A commit must not contain `- Review: user` on content the user has not reviewed at that commit.
  The reciprocal applies: a user edit to agent-reviewed content resets the agent's review attestation.
- Authorship changes to `user+agent` only when one party substantially rewrites or adds content that changes the meaning.
  Corrections, clarifications, and form-level improvements do not change authorship.
- **Editing pending sections on a file that carries user-attested sections**: the PreToolUse review-attestation hook scans the whole file for a user attestation marker and blocks any `Edit` whose `new_string` lacks a `- Review: pending` marker, even when the edit is confined to a clearly pending section (e.g. § 3 Closure).
  Correct responses: (a) use the `Write` tool to replace the file — not Edit-hook-gated; or (b) widen the `Edit` match span to include an actual `- Review: pending` metadata line so `new_string` carries it legitimately.
  Cosmetic markers inserted solely to satisfy the hook (HTML comments like `<!-- Review: pending -->`, inline prose, subtitle suffixes) are explicit anti-patterns — do not use them. Originating incident: #158 closure fill-in.

Granularity:

- **Top-section-level** metadata for devlogs: § 1 Mandate, § 2 Execution plan (both reviewed before implementation), § 3 Closure (reviewed at task closure). No file-level metadata block. Subsections inherit their top-section's metadata. See `architecture/devlog/CLAUDE.md` for the standard structure.
- **Section-level** metadata for charter documents where each section is iterated separately.
- **File-level** metadata for single-pass documents reviewed as a whole (operational files, reference lists, outcome documents).
- **Outcome documents**: Author is the mandating user (by name) — they carry liability.
  Review metadata still tracked.

### Git commit trailers [charter § 12.1]

| Section `Author` | Git commit trailer                                        |
| ---------------- | --------------------------------------------------------- |
| `agent`          | `Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`    |
| `user+agent`     | `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>` |
| `user`           | (no Claude trailer)                                       |

### Devlog updates [charter § 12.7]

Post-hoc updates to closed devlogs must be marked `[Updated DATE: summary, task number if relevant]`.
Governance updates shall be back-ported to related devlogs the same way.

### Acceptance criteria [charter § 12.7]

Tasks must define acceptance criteria in their devlog mandate before execution begins.

### Commit messages [charter § 12.7]

Short, imperative sentences.
Trailer aligned with authorship.

## Self-monitoring

### Coverage check [charter § 12.5]

At phase boundaries, check whether reasoning has gone beyond these directives.
Signal explicitly: `[outside charter scope]`.

Checkpoints:

- Execution tasks: at task start, major deliverable completion, task end
- Exploratory tasks: when summarizing findings, when transitioning to recommendations
- Large tasks: at each subtask boundary

### Ceremonies [charter § 12.5, 12.6]

Follow `CEREMONIES.md` at these trigger points:

- **Task start**: before any work begins
- **Task closure**: after final deliverable, through to finalization
- **Weekly review**: at session start if ≥1 week since last review

## Context management

### Context hygiene [charter § 12.9]

- Use `/clear` between unrelated tasks
- Delegate investigative sub-tasks to subagents
- When context is long, state what to preserve during compaction
- Keep this file under 300 lines

### Memory management [charter § 12.7]

- Update MEMORY.md after each prompt during semantically intensive sessions (conventions, decisions)
- Lower frequency for mechanical tasks
- Keep MEMORY.md concise; use separate topic files for details
- Track `last-weekly-alignment-review` date in MEMORY.md

## Architecture rules [charter § 12.8]

- Before modifying implementation or architecture, consult the axioms and exception discipline in `architecture/ARCHITECTURE.md` § 2
- No AI meta-commentary in technical documents
- Pre-define scope decisions before generation
- Define quality criteria/checklist before AI generation
- Track TBD/TBC items in TODO.md; graduate to a GH issue when the TBD blocks work or becomes actionable
- Mark unknowns as TBD/TBC, never hallucinate detail
- Cross-check AI output against source documents
- Codify design preferences explicitly

## Document governance [charter § 13]

Two-tier pipeline: Charter (principles and rules) → this file (compiled directives).
When the Charter changes, rewrite Block 3 following the compilation protocol in Block 2.
This file also contains operational conventions (Block 1) — project-specific rules not compiled from the Charter but globally compliant with it.
Devlog discipline [charter § 12.7]: every task gets a devlog entry and a GitHub issue.
Governance trace [charter § 12.5]: every devlog ends with a `## Governance trace` appendix — see `CEREMONIES.md` for format and instructions.
Resource consumption: every devlog includes a `## Resource consumption` table — see `CEREMONIES.md`.
