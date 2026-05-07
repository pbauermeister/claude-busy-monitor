# Changes

## Version 1.0.4:

- CLI: zero-count state badge foreground switched from bright black (`\x1b[90m`) to white (`\x1b[37m`) — bright black was unreadable on terminals whose palette renders it too close to true black.

## Version 1.0.3:

- README split: programmer-facing API and `make` target reference moved to new `README-LIBRARY.md`. Main README's Library subsection slimmed to a short example plus a link.
- README polish: numbered headings (level 2 and 3); macOS and `~/.claude/sessions/` mentions deduped; em-dashes replaced with `;` / `:` / parentheses; Features table dropped the redundant "No daemon, no IPC" row (already in Scope); Compatibility macOS bullet compressed to two lines.
- README example bug fix: `s.cwd` / `s.session_id` → `s.path` / `s.id`. The dataclass exposes `path` and `id`; the prior example would `AttributeError` at runtime.
- Library: improved/added docstrings on `ClaudeState`, `TokenStats`, `ClaudeSession`, `get_sessions`, `get_state_counts` (visible via `help()` and IDE hover). README-LIBRARY.md § 1 mirrors them as a fenced declarations block instead of a paraphrased table, so drift is easier to spot.
- Makefile `require` target description: "Linux/macOS only" → "Linux only" (matches the Compatibility statement).

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
