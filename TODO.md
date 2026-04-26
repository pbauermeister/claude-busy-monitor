# TODO

Recognized tasks are recorded as GitHub issues and managed in detail in corresponding `<folder>/devlog/NNNN-*.md` files.

This file captures items as they arise during work, so nothing is forgotten without diverting the current discussion or reasoning. Items collected here can later be specified as tasks, grouped together, or discarded. If a TODO item becomes significant effort, it must be turned into a standard task (GH ticket, PR, devlog).

## Won't

## TODO Items

<!-- Item 1 (build skeleton) graduated to GH issue #1 — see architecture/devlog/0001-build-skeleton.md -->
<!-- Item 1 (split monolith) graduated to GH issue #3 — see architecture/devlog/0003-split-monolith.md -->
<!-- Item 1 (test scaffold) graduated to GH issue #5 — see architecture/devlog/0005-test-scaffold.md -->

### 1. README polish

1. Main `README.md` shall be clean and engaging, like DFD or better.

### 2. PyPI publish

1. Publication to PyPI via the `Makefile` `publish` target (added in GH #1).
2. May only be called/tested by the user.

### 3. Install template for GH tickets (bug, feature request)

Gradually use GH tickets instead of TODO.md.

Later features include:

- Extract classification documentation from Python code comment sections to a separate README.
- Clarify that the classification is based on empirical findings, Claude Code version-dependant.
- Currently works for Linux. OSX support to be envisaged.
- Currently works with Claude Code v2.1.119. Version compatibility to be discussed.
