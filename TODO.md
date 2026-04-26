# TODO

Recognized tasks are recorded as GitHub issues and managed in detail in corresponding `<folder>/devlog/NNNN-*.md` files.

This file captures items as they arise during work, so nothing is forgotten without diverting the current discussion or reasoning. Items collected here can later be specified as tasks, grouped together, or discarded. If a TODO item becomes significant effort, it must be turned into a standard task (GH ticket, PR, devlog).

## Won't

## TODO Items

<!-- Item 1 (build skeleton) graduated to GH issue #1 — see architecture/devlog/0001-build-skeleton.md -->

### 1. Split monolith into installable library + CLI

1. Currently, all is implemented in `claude_busy_monitor.py`. Restructure into an installable library that programs can use as:

   ```python
   from claude_busy_monitor import (
       ClaudeSession,
       ClaudeState,
       get_sessions,
       get_state_counts,
   )
   ```

2. Library API:
   - `get_sessions() -> list[ClaudeSession]`
   - `get_state_counts() -> dict[ClaudeState, int]`

3. Shell-callable program `claude-busy-monitor` that lists a summary of states and sessions, callable by `watch`:

   ```
   0 busy   1 asking   3 idle

   d956ca8c3d42   idle   stekip-ai-mvp                 out:230.5K  in: 72.5M   33 t/s
   2be809b5f314   idle   client-py                     out:  5.5K  in:  1.1M        —
   a0e233458c35   idle   claude-busy-monitor           out:  6.0K  in:175.7K  109 t/s
   8aa45875c04f  asking  client-py                     out:  1.7K  in:279.1K        —
   ```

4. After the new structure is in place, the original `claude_busy_monitor.py` is deleted.

### 2. Test scaffold + testability discussion

1. Initial `tests/` layout and a minimal smoke test.
2. Testability discussion: what to test, fixtures vs. live `~/.claude/projects/...`, snapshot vs. structural assertions.
3. GitHub Action for tests is NOT created yet — deferred until this discussion concludes.

### 3. README polish

1. Main `README.md` shall be clean and engaging, like DFD or better.

### 4. PyPI publish

1. Publication to PyPI via the `Makefile` `publish` target (added in GH #1).
2. May only be called/tested by the user.

### 5. Install template for GH tickets (bug, feature request)

Gradually use GH tickets instead of TODO.md.

Later features include:

- Extract classification documentation from Python code comment sections to a separate README.
- Clarify that the classification is based on empirical findings, Claude Code version-dependant.
- Currently works for Linux. OSX support to be envisaged.
- Currently works with Claude Code v2.1.119. Version compatibility to be discussed.
