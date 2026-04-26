# 0007 — README polish

- GH issue: #7
- Branch: `impl/0007-readme-polish`
- Opened: 2026-04-26
- Closed: _(filled at closure)_

## 1. Mandate

- Author: agent
- Model: Claude Opus 4.7
- Review: pending

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
- Review: pending

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
- Review: pending

_(filled at closure)_

## Governance trace

_(filled incrementally)_

## Resource consumption

_(filled at closure)_
