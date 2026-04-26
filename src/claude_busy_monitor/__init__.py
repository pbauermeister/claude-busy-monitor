"""List active Claude sessions for the current user with their state."""

from importlib.metadata import version

from ._core import (
    ClaudeSession,
    ClaudeState,
    TokenStats,
    get_sessions,
    get_state_counts,
)

__version__ = version("claude-busy-monitor")

__all__ = [
    "ClaudeSession",
    "ClaudeState",
    "TokenStats",
    "__version__",
    "get_sessions",
    "get_state_counts",
]
