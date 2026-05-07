# 0017 — Tune zero-count badge colour

- GH issue: #17
- Branch: `impl/0017-zero-count-badge-colour`
- Opened: 2026-05-07
- Closed: _(filled at closure)_

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

_(filled at closure)_

## Governance trace

_(filled at closure)_

## Resource consumption

_(filled at closure)_
