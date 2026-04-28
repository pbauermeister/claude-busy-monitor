# claude-busy-monitor: library and Make reference

Programmer-facing reference for the `claude_busy_monitor` Python library and the project's `make` targets.
For installation and an overview, see [README.md](README.md).

## 1. Library API

Public names exported from `claude_busy_monitor`.

<!-- Mirrors the public symbols of src/claude_busy_monitor/_sessions.py — keep in sync -->

```python
class ClaudeState(Enum):
    """The state of a live Claude Code session.

    `str(state)` returns the lower-case state name (`"busy"`,
    `"asking"`, `"idle"`), matching each member's `value`.
    """

    BUSY = "busy"      # Processing
    ASKING = "asking"  # Awaiting the user's answer to a menu/dialog (often a permission prompt)
    IDLE = "idle"      # Awaiting the user's next prompt


@dataclass(frozen=True)
class TokenStats:
    """Cumulative token usage for one session, summed over its transcript.

    `input` includes fresh prompt tokens plus cache-create and
    cache-read tokens; counting only `input_tokens` underreports by
    roughly an order of magnitude on cached prompts.
    """

    output: int  # sum of assistant.message.usage.output_tokens
    input: int   # sum of input_tokens + cache_creation + cache_read


@dataclass(frozen=True)
class ClaudeSession:
    """One live Claude Code session as seen by the running user."""

    path: str                 # absolute project home (cwd of the claude process)
    name: str                 # last component of `path`
    id: str                   # session UUID (stem of the active JSONL file); "" if unknown
    state: ClaudeState
    stats: TokenStats | None  # None if the transcript is unreadable


def get_sessions() -> list[ClaudeSession]:
    """Return live Claude sessions for the current user, ordered by probe filename.

    Non-blocking: a single filesystem pass over `~/.claude/sessions/`
    and `~/.claude/projects/`. Requires Claude Code v2.1.119+; sessions
    from older versions are silently dropped (their probe file lacks
    the `status` field this tool relies on).
    """


def get_state_counts(
    sessions: list[ClaudeSession] | None = None,
) -> dict[ClaudeState, int]:
    """Count live sessions by state. Every `ClaudeState` key is present.

    Pass `sessions` (typically an earlier `get_sessions()` result) to
    keep counts consistent with that listing; otherwise this function
    calls `get_sessions()` itself, which re-scans the filesystem and
    may reflect a slightly later state.
    """
```

### 1.1. Example

```python
from claude_busy_monitor import get_sessions, get_state_counts, ClaudeState

# Find sessions stalled on a permission prompt and act on them.
asking = [s for s in get_sessions() if s.state == ClaudeState.ASKING]
for s in asking:
    print(f"waiting: {s.path} ({s.id[:12]})")

# Or just summarise the states.
counts = get_state_counts()
print(f"{counts[ClaudeState.BUSY]} busy, {counts[ClaudeState.ASKING]} asking")
```

Build your own: a tmux notifier, a status-bar widget, a custom dashboard.
The library exposes the same data the command uses.

## 2. Make targets

Output of `make help`:

```
Usage: make [TARGET]...

TARGETs:

 General:
  help               print this help

 Setup:
  require            install uv (idempotent; Linux only)
  venv-activate      start an interactive shell in updated .venv

 Quality:
  lint               ruff check + format-check (read-only)
  format             ruff format + lint autofix (modifies code)
  check              CI/pre-PR gate: lint unit smoke

 Tests:
  test-unit          run unit tests (fast, no I/O)
  test-smoke         run smoke tests (subprocess; no real Claude)
  test-e2e           run e2e tests (slow; drives real Claude Code)
  test               fast default tests: unit smoke

 Build and install:
  build              build wheel + sdist into dist/
  install            install in user account (CLI on ~/.local/bin/) (1)
  verify-installed   assert command present and --version matches CHANGES.md
  uninstall          uninstall from user account (1)
  verify-uninstalled assert command absent
  install-legacy     install lib user-wide (1) (2)
  uninstall-legacy   uninstall lib user-wide (1) (2)
  cycle              from scratch: uninstall clean lint tests install verify (1)

 Publish to PyPI:
  publish-quality    pre-publish gate: lint tests reinstall preflight build (1)
  publish-preflight  pre-flight safety checks for publish (no upload)
  publish            upload to PyPI (raw; use publish-quality first) (3)
  publish-tag        tag GitHub project from CHANGES.md version

 Cleanup:
  clean              remove venv, build artefacts, caches

Notes:
- All targets activate .venv for themselves.
- (1) modifies user account.
- (2) temporary hack for Python code not using venv.
- (3) prerequisite — store the PyPI token in keyring once
      (will prompt for the token):
      keyring set https://upload.pypi.org/legacy/ __token__
```
