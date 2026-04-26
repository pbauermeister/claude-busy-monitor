# Changes

## Version 0.1.0:

- Restructure into installable library + CLI.
- Public API exposed at the package root: `ClaudeSession`, `ClaudeState`, `TokenStats`, `get_sessions`, `get_state_counts`.
- CLI `claude-busy-monitor` prints a state summary line followed by one line per session, suitable for `watch`.
- `make install` installs the CLI globally via `uv tool install`.
- Versioning: `CHANGES.md` is the single source of truth — `pyproject.toml` reads it via hatch dynamic regex; `__version__` mirrors via `importlib.metadata`.

## Version 0.0.1:

- Build skeleton (`pyproject`, `venv`, `Makefile`, `ruff`, VS Code).
