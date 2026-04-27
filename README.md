# claude-busy-monitor

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)](CHANGES.md)

Live view of every [Claude Code](https://docs.claude.com/en/docs/claude-code) session on your machine — which one is **busy**, which one is **asking** for your input, which one is **idle** — with cumulative token totals.

Ships as a `claude-busy-monitor` command **and** a Python library (`get_sessions()`, `get_state_counts()`).

![claude-busy-monitor in action](https://raw.githubusercontent.com/pbauermeister/claude-busy-monitor/main/images/hero.svg)

## Why

When you run many Claude Code sessions in parallel, keeping an overview of their states is a job in itself.
You want every session **working** — every minute it isn't is time you don't get back:

- A **busy** session is the productive one — Claude is doing the work you asked for.
- An **idle** session is waiting for your next prompt — feed it.
- An **asking** session is fully stalled on a menu (most often a permission prompt) — answer it to unstuck Claude.

`claude-busy-monitor` surfaces the asking sessions instantly so they don't sit there burning your wall-clock.

## Scope

What it sees and does:

- Local Claude Code sessions of the running user (`~/.claude/sessions/` is per-user — the tool sees only your own sessions).
- Their live **state** (`busy` / `asking` / `idle`) and cumulative **token totals**.

What it deliberately does **not** do:

- **No API calls** — works entirely from local files; no quota burn, no auth needed.
- **No web or desktop sessions** — those don't write the `~/.claude/sessions/` files this tool reads.
- **No mutation, no daemon, no IPC** — read-only, ephemeral, nothing to start or supervise.

## Features

| Feature                      | What it gives you                                                                                                                                       |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **No daemon, no IPC**        | Reads the files Claude Code itself writes. Nothing to start, nothing to keep running.                                                                   |
| **Authoritative state**      | `status` comes straight from Claude Code's own probe files — no inference, no heuristics, no race-prone proxies.                                        |
| **Cache-aware token totals** | Sums all four `usage` categories (fresh, cache-create, cache-read, output). Naïvely counting only `input_tokens` underreports by ~10× on cached prompts. |
| **Summary at a glance**      | Coloured pill counts on the first line — scannable from across the room.                                                                                |
| **`watch`-friendly**         | Stable, line-oriented output; no spinners, no cursor-move escapes.                                                                                      |
| **Zero configuration**       | Reads `~/.claude/sessions/` and `~/.claude/projects/`. Nothing to set up.                                                                               |

## Install

PyPI publish is on the roadmap; until then, the install path is `git` + `make`:

```bash
git clone https://github.com/pbauermeister/claude-busy-monitor.git
cd claude-busy-monitor
make require   # installs uv if missing (idempotent; Linux/macOS)
make install   # installs the command globally via `uv tool install .`
```

Only prerequisite is Python 3.11+; `make require` bootstraps [`uv`](https://github.com/astral-sh/uv) for you.

To work on the project itself rather than just use it, run `make venv-activate` instead — it creates `.venv`, syncs dev deps, and drops you into an activated shell.
`make help` lists every Makefile target (lint, format, test-unit / smoke / e2e, build).

## Usage

### Command

```bash
claude-busy-monitor                       # one-shot listing
watch -n 1 -c claude-busy-monitor         # live refresh (the -c keeps colours)
```

The output is one summary line followed by one line per session.
Each session line reads:

| Column | Meaning                                                       |
| ------ | ------------------------------------------------------------- |
| 1      | session id (first 12 hex chars)                               |
| 2      | state pill — `busy` (red) / `asking` (yellow) / `idle` (green) |
| 3      | working directory (basename)                                  |
| 4      | output tokens, cumulative (`out:`)                            |
| 5      | input tokens, cumulative (`in:` — fresh + cached, summed)     |

### Library

Build your own: a tmux notifier, a status-bar widget, a custom dashboard. The library exposes the same data the command uses.

```python
from claude_busy_monitor import get_sessions, get_state_counts, ClaudeState

# Find sessions stalled on a permission prompt and act on them.
asking = [s for s in get_sessions() if s.state == ClaudeState.ASKING]
for s in asking:
    print(f"waiting: {s.cwd} ({s.session_id[:12]})")

# Or just summarise the states.
counts = get_state_counts()
print(f"{counts[ClaudeState.BUSY]} busy, {counts[ClaudeState.ASKING]} asking")
```

Public API: `ClaudeSession`, `ClaudeState`, `TokenStats`, `get_sessions()`, `get_state_counts()`.

## How it works

`claude-busy-monitor` reads two on-disk sources that Claude Code itself writes:

1. `~/.claude/sessions/<pid>.json` — one probe file per live session, with the authoritative `status` field (`busy` / `idle` / `waiting`).
2. `~/.claude/projects/<encoded-cwd>/<sid>.jsonl` — the per-session transcript, used only to total token usage.

State classification is a one-row table — no inference, no heuristics.
Token usage sums the four `usage` categories per assistant entry.

For the full design — assumptions the classifier depends on, diagnostic recipes for when something looks wrong, and the repair playbook — see [README-STATE-DETECTION.md](README-STATE-DETECTION.md).

## Compatibility

- **Operating system**: Linux (relies on `/proc/<pid>/comm`).
  macOS is not supported yet — collaboration is very welcome.
  Please start by [opening a Discussion](https://github.com/pbauermeister/claude-busy-monitor/discussions) so we can align on the approach before any issue or PR.
- **Claude Code**: v2.1.119 introduced the `status` field this tool relies on; older versions are silently dropped.
  `/exit` and `claude --resume <sessionId>` will migrate them.

## License

[MIT](LICENSE) — see [CHANGES.md](CHANGES.md) for the version history.
