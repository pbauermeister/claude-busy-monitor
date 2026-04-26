# TODO

Recognized tasks are recorded as GitHub issues and managed in detail in corresponding `<folder>/devlog/NNNN-*.md` files.

This file captures items as they arise during work, so nothing is forgotten without diverting the current discussion or reasoning. Items collected here can later be specified as tasks, grouped together, or discarded. If a TODO item becomes significant effort, it must be turned into a standard task (GH ticket, PR, devlog).

## Won't

## TODO Items

### 1. Scaffolding this GitHub project.

1. The goal of this repo is to create a Python library and program providing the following:
   - The library provides `get_sessions() -> list[ClaudeSession]`
     and `get_state_counts() -> dict[ClaudeState, int]`
   - The program lists a summary of states and sessions, that can be called by `watch`:

     ```
     0 busy   1 asking   3 idle

     d956ca8c3d42   idle   stekip-ai-mvp                 out:230.5K  in: 72.5M   33 t/s
     2be809b5f314   idle   client-py                     out:  5.5K  in:  1.1M        —
     a0e233458c35   idle   claude-busy-monitor           out:  6.0K  in:175.7K  109 t/s
     8aa45875c04f  asking  client-py                     out:  1.7K  in:279.1K        —
     ```

2. Currently, all is implemented in `claude_busy_monitor.py`. The goal is to structure this repo to provide:
   - An installable library, that programs can use as:
     ```
     from claude_busy_monitor import (
         ClaudeSession,
         ClaudeState,
         get_sessions,
         get_state_counts,
     )
     ```
   - A shell-callable program: `claude-busy-monitor`.
   - After all the created structure is created, the original `claude_busy_monitor.py` has to be deleted.

3. A build system, inspired from project `/home/pascal/dev-pb/dfd` (aka DFD).

4. Publication to PyPi. May only be called/tested by the user.

5. All development, including test, lint and publication shall be managed by the `Makefile`.
   - For development, Python virtual env targets are provided to create/enter venv
   - For development, `require` target installs the requirements (supposing venv activated)

6. Lint and reformatting shall use `ruff`.

7. Build may be inspired by project DFD, or a more modern pattern.

8. A GitHub action shall not yet be created for tests, as testability must be first discussed.

9. The main README.md shall be clean and engaging, like DFD or better.

10. For vscode, format-on-save: for Python with ruff, for markdown with prettier.
