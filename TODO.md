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

   d956ca8c3d42   idle   my-ai-project                 out:230.5K  in: 72.5M
   2be809b5f314   idle   client-py                     out:  5.5K  in:  1.1M
   a0e233458c35   idle   claude-busy-monitor           out:  6.0K  in:175.7K
   8aa45875c04f  asking  client-py                     out:  1.7K  in:279.1K
   ```

4. Split and redistribute the code and documentation:
   - Library code originally in `claude_busy_monitor.py` shall live in a proper library package. It shall contain no rendering code (colors).
   - The state detection documentation originally in `README-STATE-DETECTION.md` shall be updated so that agents can continue to maintain/fix the state classification.
   - Shell-callable program shall use the library, and care for rendering (ANSI terminal, `watch` friendly, so base-ANSI colors).

5. Add a `make install` target installing the CLI globally via `uv tool install .` (puts `claude-busy-monitor` on `~/.local/bin/`, so the program runs outside the dev venv).

6. Versioning: `CHANGES.md` is the single source of truth for version number and summary (DFD pattern). Each release is a `## Version X.Y.Z:` heading followed by a bullet-list summary. The build derives the version from this file (modern equivalent: hatch dynamic version via `[tool.hatch.version] source = "regex" path = "CHANGES.md"`, with `version` declared as dynamic in `[project]`). `claude_busy_monitor.__version__` mirrors the same source. Bumping a version means appending a new heading + summary in `CHANGES.md` — no separate edit to `pyproject.toml` or `__init__.py`.

7. After the new structure is in place, the original `claude_busy_monitor.py` is deleted.

### 2. Test scaffold + testability discussion

1. Initial `tests/` layout and a minimal smoke test.
2. Testability discussion: what to test, fixtures vs. live `~/.claude/projects/...`, snapshot vs. structural assertions.
3. Conventions to adopt (simplified for this project's scope):
   - **Test categories** distinguished: **unit** (pure-compute, no I/O — e.g. classifier given fake inputs → expected outputs), **smoke** (entry-point runs, package imports, CLI exits 0), **scenario** (drive a real Claude Code session on a fake project through scripted prompts, assert classifier output against expected state — slow, end-to-end). Skip a tamper harness and a non-regression suite — over-engineered for this scale.
   - **Naming**: descriptive, active voice, present tense (e.g. `test_classifier_busy_when_marker_present`, `test_cli_runs_and_exits_zero`); no modal verbs (`should`, `must`, `shall`); assertion messages match the test name in plain English.
   - **Module layout**: one module per topic (`tests/test_<topic>.py`), `@pytest.fixture(scope="module") state` for shared setup, one assertion per `test_*` function (multi-assertion fine when the assertions describe one behaviour).
   - **Makefile as stable interface**: `make test-unit`, `make test-smoke`, `make test-scenario`, `make test-full` (default fast subset = unit + smoke; scenario tests run separately because they spawn a real Claude session). What runs behind each target is internal (pytest, shell, mix); contributors and CI call the Makefile target.
4. GitHub Action for tests is NOT created yet — deferred until this discussion concludes.

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
