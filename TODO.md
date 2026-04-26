# TODO

Recognized tasks are recorded as GitHub issues and managed in detail in corresponding `<folder>/devlog/NNNN-*.md` files.

This file captures items as they arise during work, so nothing is forgotten without diverting the current discussion or reasoning. Items collected here can later be specified as tasks, grouped together, or discarded. If a TODO item becomes significant effort, it must be turned into a standard task (GH ticket, PR, devlog).

## Won't

## TODO Items

<!-- Item 1 (build skeleton) graduated to GH issue #1 — see architecture/devlog/0001-build-skeleton.md -->
<!-- Item 1 (split monolith) graduated to GH issue #3 — see architecture/devlog/0003-split-monolith.md -->

### 1. Test scaffold + testability discussion

1. Initial `tests/` layout and a minimal smoke test.
2. Testability discussion: what to test, fixtures vs. live `~/.claude/projects/...`, snapshot vs. structural assertions.
3. Conventions to adopt (simplified for this project's scope):
   - **Test categories** distinguished: **unit** (pure-compute, no I/O — e.g. classifier given fake inputs → expected outputs), **smoke** (entry-point runs, package imports, CLI exits 0), **e2e** (end-to-end: drive a real Claude Code session on a fake project through scripted prompts — simulating a user without a GUI — and assert classifier output against expected state; slow). Skip a tamper harness and a non-regression suite — over-engineered for this scale.
   - **Naming**: descriptive, active voice, present tense (e.g. `test_classifier_busy_when_marker_present`, `test_cli_runs_and_exits_zero`); no modal verbs (`should`, `must`, `shall`); assertion messages match the test name in plain English.
   - **Module layout**: one module per topic (`tests/test_<topic>.py`), `@pytest.fixture(scope="module") state` for shared setup, one assertion per `test_*` function (multi-assertion fine when the assertions describe one behaviour).
   - **Makefile as stable interface**: `make test-unit`, `make test-smoke`, `make test-e2e`, `make test-full` (default fast subset = unit + smoke; e2e tests run separately because they spawn a real Claude session). What runs behind each target is internal (pytest, shell, mix); contributors and CI call the Makefile target.
4. GitHub Action for tests is NOT created yet — deferred until this discussion concludes.

### 2. README polish

1. Main `README.md` shall be clean and engaging, like DFD or better.

### 3. PyPI publish

1. Publication to PyPI via the `Makefile` `publish` target (added in GH #1).
2. May only be called/tested by the user.

### 4. Install template for GH tickets (bug, feature request)

Gradually use GH tickets instead of TODO.md.

Later features include:

- Extract classification documentation from Python code comment sections to a separate README.
- Clarify that the classification is based on empirical findings, Claude Code version-dependant.
- Currently works for Linux. OSX support to be envisaged.
- Currently works with Claude Code v2.1.119. Version compatibility to be discussed.
