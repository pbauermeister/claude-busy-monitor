# Changes

## Version 1.0.2:

- README install section restructured by user intent: **As a command** (recommends `pipx install` / `uv tool install` — isolated per-tool venv, no PEP 668 grief), **As a library** (`pip install` in project venv), **From source** (contributors). The previous wording suggested bare `pip install claude-busy-monitor` which fails on modern PEP 668-marked distros (Debian 12+, Ubuntu 23+, etc.).

## Version 1.0.1:

- README install section now leads with `pip install` / `uv tool install` from PyPI (project is live there).
- README tagline corrected: "your Claude Code sessions" instead of "every Claude Code session" — `~/.claude/sessions/` is per-user, the tool sees only the running user's sessions.
- Makefile `publish-quality` recipe now refreshes the editable `.venv` install (`uv sync --reinstall-package`) before lint/tests so a just-bumped CHANGES.md version is reflected in `__version__` — fixes the silent test-version-mismatch failure mode after a version bump.
- Makefile `publish-tag` doc string clarified: "tag GitHub project from CHANGES.md version" (drops the misleading `(1)` user-account marker — publish-tag only touches local + origin git refs, not the user account).

## Version 1.0.0:

- Promote from alpha to stable. Public API frozen — semver guarantees apply from now on.
- No functional changes from `0.1.0.post1`.

## Version 0.1.0.post1:

- README hero image now uses an absolute GitHub-raw URL so it renders on PyPI (relative paths don't resolve in the PyPI project description).

## Version 0.1.0:

- Restructure into installable library + CLI.
- Public API exposed at the package root: `ClaudeSession`, `ClaudeState`, `TokenStats`, `get_sessions`, `get_state_counts`.
- CLI `claude-busy-monitor` prints a state summary line followed by one line per session, suitable for `watch`.
- `make install` installs the CLI globally via `uv tool install`.
- Versioning: `CHANGES.md` is the single source of truth — `pyproject.toml` reads it via hatch dynamic regex; `__version__` mirrors via `importlib.metadata`.

## Version 0.0.1:

- Build skeleton (`pyproject`, `venv`, `Makefile`, `ruff`, VS Code).
