# Ceremonies

- Author: user+agent
- Review: user

Companion to `CLAUDE.md`. Read and follow at trigger points defined
there. This file is not auto-loaded — the agent reads it explicitly.

## Task start

Before any work begins on a new task:

1. **Weekly-review offer (preflight)**: check `last-weekly-alignment-review` in `MEMORY.md`. If ≥ 7 days have elapsed AND the offer was not already declined today, offer the weekly review to the user before starting. User may accept (run the review first, then return to this task), defer (proceed with task, offer again next session), or decline (record that the offer was declined today, proceed).
2. **Git state check**: check for uncommitted changes, untracked files, or other loose state — propose tidying up before proceeding
3. **GH issue**: ask the user for an existing ticket number; if none, create one with the proper `[gov]`/`[arch]`/`[impl]` prefix
4. **Branch and devlog**: create the task branch and devlog entry (`<folder>/devlog/NNNN-short-description.md`) [charter § 12.7]
   - Record `- Opened: YYYY-MM-DD` in the devlog header (immediately after the `- GH issue:` and `- Branch:` lines). This date is the primary source of truth for wall-clock duration later — squash-merges erase commit dates, so the devlog header is the only durable record.
5. Identify task nature: exploratory or execution [charter § 12.2]
6. Assess criticality: aggressive automation vs. strict human oversight [charter § 12.4]
7. Scope check: flag if too vague, too broad, or not granular enough [charter § 12.4]
   - For exploratory tasks: prefer broad mandates over specific deliverables — premature scoping causes rework (lesson from WP-2.1 rescoping, #32)
   - For execution mandates: include a verification deliverable (smoke test, healthcheck, or equivalent) alongside design deliverables (lesson from WP-2.2, #35)
8. Input documents: mandate must list input documents and links relevant to the task [charter § 12.7]
9. **Test plan** (execution tasks): mandate must include a test plan — what will be tested, how, and at what scale. Exploratory tasks are exempt.
10. **Test strategy discussion** (all tasks, at mandate time): discuss and capture the test strategy independently from implementation choices — what will convince us the outcome is correct, which invariants matter, which failure modes deserve coverage. The discussion is exploratory and upstream of step 9's concrete plan; it probes testability early so the plan has more to work with. **No hard gate**: if no specific strategy emerges at mandate time, record "no specific strategy surfaced at mandate time" and proceed.
11. Watchlist reminder: remind the user of the active watchlist (devlog 0007 § 3.2) [charter § 12.5]
12. Coverage check: confirm operating within charter scope [charter § 12.5]
13. **Commit and review**: commit the devlog with the mandate, ask the user to review
14. **Mandate approval gate**: the user must affix their review attestation on the mandate section and commit it before any implementation begins. Standard-flow default; the fast-path carve-out for mechanical tasks with pre-existing scope (see § Fast-path task flow) shifts all three attestations to closure without dropping them. The user bears accountability and may have requirements the agent did not anticipate.
    - Devlogs carry review metadata at two levels: mandate section (reviewed here, before implementation) and file-level at top of file (reviewed at closure). Other sections inherit the file-level metadata.
15. **Implementation plan** (non-trivial implementation tasks): consult `implementation/HOWTO-DEVELOP.md` for established procedures, then produce a detailed plan in the devlog before writing code — files created/modified, key design decisions. Purpose: the user bears accountability for generated code and needs the opportunity to spot tensions with existing architecture before code is written. Commit and review before implementation begins. Style discussions happen in the debrief.
16. **Create PR**: create the PR with `Closes #N` in the description referencing the associated GH issue

## Task closure

Most closure outputs are recorded in the task devlog; per-step instructions say where.
After the final deliverable:

1. **Record `- Closed: YYYY-MM-DD`** in the devlog header. Do this first, so the closing commit carries the correct date — squash-merges will erase commit dates, the devlog header is the durable record.
2. Commit all pending changes before requesting review [charter § 12.7]
3. Review request: provide specific list of places to review (file paths, sections, changed lines) [charter § 12.4]
   - Implementation tasks: include a file inventory (files created/changed) — informational, verifiable from the PR diff
4. Coverage check: confirm reasoning stayed within charter scope [charter § 12.5]
5. **Test update** (implementation tasks): consult the devlog `### Verification commands` section and incorporate commands not yet covered into the appropriate test category (see `implementation/HOWTO-TEST.md`).
6. **Test coverage review** (tasks that change code): consult the devlog `### 3.5 Test coverage review` subsection. For each code change or refactoring made during the task, decide one of: (a) covered by an existing test — note which, (b) add a new test — the test must also exercise the pre-change code so it would have caught the original failure mode, (c) justify absence — test not worth writing here (e.g. pure prose change, one-off script). Record the decisions in § 3.5.
   This is distinct from step 5 (Test update): step 5 ports _verification commands_ the task produced into the suite; step 6 asks the reverse question — did the task's _own changes_ warrant coverage?
7. **Gate check**: before proceeding to retrospective, explicitly verify all closure gates — acceptance criteria met, all deliverables committed, user approvals for critical items obtained. If any gate fails, resolve before continuing.
   - Implementation tasks: `make test` must pass
8. Task retrospective: draft as a voting table for user review [charter § 12.6]:

   | #   | Point             | Agent | User     |
   | --- | ----------------- | ----- | -------- |
   | 1   | (example finding) | well  | surprise |

   Values: well / not well / surprise / don't care.
   Disagreements trigger discussion; don't care items kept as calibration data — recurrence across tasks may graduate them.

   Categories to cover: what went well, what didn't go as planned (distinguish genuine problems from productive refutations), challenge rules, challenge ourselves, effort/ROI, outcome relevance, task validity.

9. **Demo scenario** (implementation tasks): include a replayable demo section in the devlog — numbered steps with commands and curated output excerpts.
   - Self-sufficient: builds, starts, seeds its own data, shows the interesting bits, stops
   - Replayable at the PR merge commit hash (checkout that hash, follow the steps)
   - Not maintained — it is a snapshot of what the task achieved; bitrot is acceptable
10. **Update HOWTO-USE.md** (implementation tasks): if the task changes operational behaviour (new commands, new endpoints, changed workflows), update the operational usage guide and its document history.
    - Generic (not task-specific), maintained, shorter than the demo
    - Tests and HOWTO-USE.md are maintained; the demo scenario is not
11. Forward-looking check: does this output well-serve the next task? Acceptance criteria are backward-looking; this complements them by checking whether the deliverable is a good foundation for successor tasks.
12. **Operational metrics**: populate the devlog's `## Resource consumption` table (see § Resource consumption below for the format). In addition to tokens and wall time, record per-task counters: pre-commit hook failures, subagent invocations, `/clear` events, memory rotation events, and LOC/files changed (from `git diff main...branch`). Manual estimates are acceptable — precision is not billing-grade.
13. **Update MEMORY.md Current State**: mark completed tasks, remove stale entries, verify accuracy against actual GH issue states
14. **Capture new conventions**: if any practice was established or refined during this task, codify it in the appropriate file (CLAUDE.md, CEREMONIES.md, or MEMORY.md)
15. **User review (non-delegable)** [hook-enforced]: user affixes `- Review: user` attestations and commits — agent must not perform this step
16. **Finalization**:
    - Agent: push branch, ask user to merge
    - User: merge PR (this auto-closes the linked issue via `Closes #N` in the PR description)
    - Agent: delete local branch, checkout `main`, pull

## Fast-path task flow

A lightweight variant of § Task start + § Task closure for mechanical, well-scoped tasks.
Preserves every audit artefact (devlog with three sections, user attestations, PR, hooks) but compresses _when_ they happen: scope is already in git (as a TODO item, ceremony definition, or explicit user brief), work happens with conversational approval, and the devlog is written in one pass at closure.

### Eligibility (all three must hold)

1. **Scope comes from a pre-existing artefact**: a `TODO.md` item, a ceremony definition (e.g. § Weekly alignment review), or an explicit user brief captured in chat.
2. **Mechanical or well-understood**: no design decisions, no architectural implications, no cross-cutting change.
3. **Scope fits in one paragraph** and cannot plausibly drift during implementation.

If any condition fails, use standard flow (§ Task start + § Task closure).

### Flow

1. **Fit-check in chat**: agent names the scope source (`TODO #N`, ceremony name, or brief) and proposes fast-path; user confirms or amends.
2. **GH issue, branch, PR**: same artefacts as standard flow. PR title MAY mark fast-path explicitly (e.g. `[gov] [fast-path] ...`).
3. **Implement** with conversational approval and per-commit diff review. All hooks fire as usual.
4. **Devlog in one shot at closure**:
   - § 1 Mandate quotes the scope source verbatim + a one-liner "accepted on `<date>`" + any chat amendments.
   - § 2 Execution plan describes the actual steps taken (rather than planned).
   - § 3 Closure covers deviations, verification, retrospective, verdict as usual.
5. **User attests all three sections together** and commits.
6. **User merges PR.**
7. **Agent cleanup**: delete local branch, checkout `main`, pull.

### Doc-only carve-out

When the task touches only Markdown files (no code, no tests, no scripts, no config), the deliverable _is_ the reviewed document and parts of the devlog would paraphrase it. The following devlog subsections MAY be dropped:

1. § 3.2 File inventory — the PR diff is the inventory.
2. § 3.3 Verification — rendering on the PR + manual cross-ref check is the verification; record only if non-obvious checks were done.
3. § 3.5 Verdict rationale — a bare "Accept / Reject / Accept with reservations" recommendation suffices; rationale is in the deliverable itself.

Remain mandatory (cross-task-analysable structure):

1. § 1 Mandate and § 2 Execution plan — the "what was changed and why" record.
2. § 3.1 Deviations — captures design pivots.
3. § 3.4 Retrospective — voting data feeds cross-task analysis.
4. Governance trace — clause-level attribution.
5. Resource consumption — phase / counter tables.

Applies inside fast-path flow only. Standard-flow doc tasks keep the full structure.

### Non-eligible (keep in standard flow)

- Tasks with design decisions (language choice, architecture, data-model shape).
- Tasks that touch multiple top-level directories or structural interfaces.
- Weekly alignment review and factoring review: ceremony-defined scope but outcomes require judgement and often surface follow-ups.
- Incident-driven fixes where the cause is not yet understood.
- First-of-kind tasks (when a new convention is being established).

### Fallback

Fast-path eligibility is a judgement call at task start, not a hook-enforced gate. If during implementation the scope turns out to exceed fast-path criteria (unexpected design decision surfaces, work sprawls), revert to standard flow: pause, write § 1 and § 2 explicitly, commit and review before continuing.

## Weekly alignment review

At session start, if ≥1 week since last review (check MEMORY.md for
`last-weekly-alignment-review` date):

1. Propose review to user — ask for confirmation before proceeding
2. If confirmed:
   - Internal drift assessment against Charter § 12 rules
   - External landscape scan (tools, models, practices)
   - Memory audit per `HOWTO-MEMORY-AUDIT.md` — tag each memory file, resolve tensions, graduate transfer-candidates, delete redundant cache, verify `MEMORY.md` is under its size limit
   - Verify all `HOWTO*.md` guides are reachable from a `CLAUDE.md` (directly or via an index like `HOWTO-DEVELOP.md`)
   - Remind to run the **Factoring review** ceremony (see § Factoring review below) — schedule or run in the same session if candidates have accumulated
   - Update `last-weekly-alignment-review` in MEMORY.md
3. If deferred: offer to create a separate task

## Factoring review

A recurring ceremony that consumes the `## Factoring candidates` appendix entries accumulated in devlogs since the last Factoring review. The Weekly alignment review reminds the agent to run or schedule it; it is a standalone ceremony, not a sub-step.

Known requirements (to be refined during the first effective ceremony):

- **Inputs**:
  - _Passive_: every `## Factoring candidates` appendix across recent devlogs (grep over `*/devlog/*.md` since the last Factoring review date) — what the agent happened to notice during per-task work.
  - _Active (optional, mandated per ceremony)_: a thorough codebase scan for duplication, recurring parameters, and parallel shapes — surfacing patterns that per-task work wouldn't have noticed. Trades review cost for broader coverage. Candidate scan targets: identical or near-identical function bodies across modules, recurring literal values/strings/paths, similar error-handling blocks, parallel data-shape transformations. May be subagent-assisted.
- **Outputs**: a clustered, prioritised list of candidate factorings, recorded in `architecture/FACTORING-TODO.md`. Top items graduate to tasks (`[impl]`); low-value or unsound candidates move to the file's `## Won't` section with a one-line reason.
- **Persistence file** — `architecture/FACTORING-TODO.md`: mirrors the root `TODO.md` convention (priority-ordered pending list + `## Won't` section with rationale). Survives across Factoring reviews. Each review reads prior state, merges new inputs, updates the file, and schedules graduated tasks. **Won't entries are excluded from subsequent passive collection and active scans** — known-Won't items are neither re-searched nor re-proposed.
- **Clustering**: group candidates that point at the same underlying duplication or parameter pattern. Count hits per cluster — higher hit counts mean stronger signal.
- **Prioritisation heuristics**: (a) hit count; (b) number of distinct files affected; (c) whether a related task is already queued; (d) human-maintainability gain vs. refactor cost.
- **Discard rationale**: a candidate may be rejected (e.g. rule-of-three not yet met, indirection cost outweighs gain, scope creep risk) — record the reason under `## Won't` in `architecture/FACTORING-TODO.md`. The rationale is the memory that prevents future reviews from re-investigating the same item.
- **Process shape** (open questions to resolve during first execution): subagent-assisted scan vs. manual pass; whether the output is a devlog outcome document; whether graduated tasks get bundled or split.
- **Cadence**: initial default is "alongside the Weekly alignment review when candidates have accumulated". Adjust after the first execution based on candidate-arrival rate and review cost.
- **Tracking**: when the first factoring review runs, add a `last-factoring-review` date to MEMORY.md alongside `last-weekly-alignment-review`.

The exact cadence, tooling, and output format will be refined during the first effective Factoring review. This section is a scaffold, not a spec.

## Governance trace appendix

Every task devlog ends with a `## Governance trace` appendix — a structured log of which governance clauses the agent consulted, applied, or that created tension during the task.

### Purpose

1. Survive context compaction and memory loss — the trace is in the devlog, not in agent memory
2. Enable evidence-based governance effectiveness reports — which clauses are load-bearing, which create friction, which are dead weight

### When to populate

- **During the task**: append entries as clauses are consulted or create tension. Do not batch — log incrementally so the trace survives mid-task context loss.
- **At closure**: review the trace for completeness before requesting user review.

### Format

The appendix is a Markdown table at the end of the devlog, after the retrospective:

```markdown
## Governance trace

| Source                             | Clause                | Action  | Note                                   |
| ---------------------------------- | --------------------- | ------- | -------------------------------------- |
| CLAUDE.md:152                      | YAGNI                 | applied | ruled out presentation-spec layer      |
| CEREMONIES.md:26                   | mandate approval gate | applied | user reviewed before implementation    |
| CLAUDE.md:87                       | naming discipline     | tension | "validate" vs "snapshot" naming debate |
| CEREMONIES.md:44                   | task retrospective    | applied | voting table format                    |
| implementation/HOWTO-DEVELOP.md:10 | entity guide          | skipped | not applicable — no new entity         |
```

### Fields

- **Source**: file path and line number (at time of task execution). Line numbers may drift as files evolve — the clause name provides resilience.
- **Clause**: short name of the clause (human-readable, stable across line renumbering).
- **Action**: one of:
  - `applied` — clause followed as intended
  - `tension` — clause created friction, required interpretation, or was debated. In Note, state the resolution: mundane (resolved in-task), escalated (→ TODO or GH issue), or unaddressed.
  - `created` — new clause or convention emerged during this task
  - `skipped` — clause was relevant but consciously not applied (with reason in Note)
  - `todo` — a TODO.md item was captured during this task related to a governance clause. Note should reference the TODO item number.
- **Note**: brief context. For `tension` entries, state the tension and resolution.

### Retroactive reconstruction

For devlogs created before this convention, the trace is reconstructed from devlog content and the governance file state at the time of the associated PR merge.
Reconstructed entries carry a confidence indicator in the Note column: `[high]`, `[medium]`, or `[low]`.

## Governance effectiveness report

Accumulated traces across devlogs feed governance effectiveness reports.
Produce an effectiveness report at each weekly alignment review as an `--outcome` document of the weekly review devlog.

### Analysis tool

`governance/scripts/analyse_governance_traces.py` — parses all devlog trace tables and produces the report sections below.
Run: `python3 governance/scripts/analyse_governance_traces.py`

### Report sections

The report follows this fixed structure for maximum reproducibility:

1. **Coverage** — time span, tasks span, total entries, reconstruction method.
2. **Tier-level shares** — CLAUDE.md vs CEREMONIES.md vs HOWTO-\*.md. Include CLAUDE.md block split (Block 1 vs Block 3). Semigraphics bar chart.
3. **File-level shares** — per MD file with bar chart.
4. **Charter back-tracking** — one combined table with columns: Charter section (with title), Block 3 count, Block 1 count, cumulative total. Charter section titles must match `AI-AUGMENTED-ENGINEERING-CHARTER.md` — verify and update the script's `CHARTER_TITLES` dict if the Charter changes.
5. **Clause-level detail** — four sub-sections:
   - 5.1: most applied clauses (top 15, bar chart, descending)
   - 5.2: tension hotspots (all, bar chart, descending)
   - 5.3: created clauses by task (ascending by task number — chronological, showing governance evolution)
   - 5.4: never-referenced clauses (qualitative assessment)
6. **Period summary** — action breakdown by era (bar chart), what is easy/hard/impossible to codify.
7. **Trends** — five sub-sections:
   - 7.1: governance maturity (creation vs application share by era, bar chart)
   - 7.2: entries per task by era
   - 7.3: task type share per era (gov vs arch/impl vs study vs product, bar chart)
   - 7.4: Charter section evolution across eras (one unified table: each Charter section with per-era sub-rows showing ratio = entries/tasks, bar chart. Sorted by § 4 total.)
   - 7.5: trends conclusion — cross-reference § 7.3 (what each era focused on) with § 7.4 (how Charter sections evolved) to interpret the governance trajectory. Identify deepening-process vs internalised-habit patterns.

All tables sorted in descending order unless noted otherwise (§ 5.3 is chronological).
Semigraphics bar charts (`█░`) used wherever a ratio or progression needs to be scannable.

### Charter back-tracking method

Two-step tracing:

1. Traces reference MD files (CLAUDE.md, CEREMONIES.md, HOWTO-\*.md) — the agent's working documents.
2. The report resolves to Charter sections via two maps in the analysis script:
   - `BLOCK3_CHARTER_MAP`: direct mapping via `[charter § 12.X]` tags already in CLAUDE.md.
   - `BLOCK1_CHARTER_MAP`: conceptual alignment (e.g. YAGNI → § 12.4, naming → § 12.8).
   - CEREMONIES.md entries: currently unmapped (future: add Charter tags to CEREMONIES.md).
   - `CHARTER_TITLES`: must match `AI-AUGMENTED-ENGINEERING-CHARTER.md` headings. Verify when Charter changes.

## Operational metrics report

Aggregates the per-task `## Resource consumption` data (header `- Opened:` / `- Closed:` dates, token/time table, counter table — instrumentation codified in #138) into cross-task rollups.
Complements the Governance effectiveness report: traces tell _what fired_; operational metrics tell _how the project breathes_.

### Cadence

Proposed at each weekly alignment review alongside the Governance effectiveness report.
**MAY be skipped** — if the user judges the rollup would not add signal yet (early data, no changes since last report), the offer is recorded as declined and the next review is the next opportunity.

### Report sections

1. **Backlog item velocity** — created → addressed lag, by task type.
2. **Friction-to-codification lag** — time between a governance-trace `tension` entry and the rule that emerges from it (if any).
3. **Task type distribution drift** — gov / arch / impl / study / product share per era.
4. **Wall-clock duration distribution** — `Closed - Opened` histogram; LOC / files-changed histograms.
5. **Hook-failure and subagent-invocation rates** — per task type.
6. **Counter anomalies** — any task with outlier values (e.g., many pre-commit hook fails, `/clear` events, memory rotations).

### Preconditions

- At least ~5 tasks closed under the #138 instrumentation since the last report (otherwise the aggregate is noise).
- If fewer, the review records the fact and defers to the next cycle.

### Output

An `--outcome-` document next to the weekly-review devlog (same pattern as the Governance effectiveness report).

### Tooling

No aggregator script exists yet (unlike the effectiveness report's `governance/scripts/analyse_governance_traces.py`). Building one is intentionally deferred: when the report is first accepted at a weekly review, construction of the analyzer becomes the task that produces the first report. Until then the offer is recorded as "deferred (tooling TBD)" and resurfaces next review. No standing TODO item — the ceremony itself is the reminder.

## Resource consumption

Every task devlog includes a `## Resource consumption` section at the end, recording approximate token/time usage per phase plus per-task operational counters.

### Purpose

1. Track the cost of governance and development activities over time
2. Identify which task types or phases are token-intensive
3. Capture operational signals that cannot be reconstructed after the fact (hook failures, subagent invocations, `/clear` events, memory rotations)
4. Feed into cost/value analysis alongside governance effectiveness data

### When to capture

- **At phase boundaries**: note approximate token count when transitioning between mandate, implementation, closure, etc.
- **Subagent usage**: captured from subagent result metadata (`total_tokens`, `duration_ms`) — these are precise.
- **Main conversation**: approximate, based on context window state at phase boundaries.
- **Counters**: capture incrementally as events occur during the task; tally at closure (step 12 of Task closure).

### Format

Two tables at the end of the devlog, after the governance trace:

```markdown
## Resource consumption

| Phase          | Tokens (approx) | Wall time  |
| -------------- | --------------- | ---------- |
| Mandate        | ~25k            | 20 min     |
| Implementation | ~180k           | 2 h        |
| Closure        | ~40k            | 30 min     |
| Subagents      | ~120k           | (parallel) |
| **Total**      | **~365k**       | **~3 h**   |

| Counter                | Value                       |
| ---------------------- | --------------------------- |
| Pre-commit hook fails  | N                           |
| Subagent invocations   | N                           |
| `/clear` events        | N                           |
| Memory rotation events | N                           |
| LOC changed            | N (from `git diff main...`) |
| Files changed          | N                           |
```

### Precision

- Subagent tokens: precise (from result metadata).
- Main conversation tokens: order-of-magnitude useful, not billing-grade.
- No retroactivity: token counts are ephemeral, only available during the session. Past tasks cannot be measured.

## Experimental

Provisional practices to try. Items here are not yet codified in the
Charter — they are trialed during ceremonies and evaluated at weekly
reviews.

(No items yet.)
