"""Command-line entrypoint for `claude-busy-monitor`.

Prints a state summary line followed by one line per Claude session.
ANSI palette is base-16 — `watch`-friendly.
"""

import argparse
from enum import StrEnum

from claude_busy_monitor import ClaudeState, get_sessions, get_state_counts


class Ansi(StrEnum):
    """ANSI escape sequences used by the CLI palette."""

    RESET = "\x1b[0m"

    FG_BLACK = "\x1b[30m"
    FG_GREY = "\x1b[90m"

    BG_BLACK = "\x1b[40m"
    BG_RED = "\x1b[41m"
    BG_GREEN = "\x1b[42m"
    BG_YELLOW = "\x1b[43m"

    FX_BLINK = "\x1b[5m"


_STATE_STYLE: dict[ClaudeState, str] = {
    ClaudeState.BUSY: f"{Ansi.FG_BLACK}{Ansi.BG_RED}",
    ClaudeState.ASKING: f"{Ansi.FG_BLACK}{Ansi.BG_YELLOW}{Ansi.FX_BLINK}",
    ClaudeState.IDLE: f"{Ansi.FG_BLACK}{Ansi.BG_GREEN}",
}


def _colorize(text: str, state: ClaudeState, doit: bool = True) -> str:
    """Wrap `text` in the ANSI style defined for `state`."""
    if not doit:
        return f"{Ansi.BG_BLACK}{Ansi.FG_GREY}{text}{Ansi.RESET}"
    return f"{_STATE_STYLE[state]}{text}{Ansi.RESET}"


def _humanize_count(n: int) -> str:
    """Short human-readable integer: 12345 → '12.3K', 4_567_890 → '4.6M'."""
    if n < 1000:
        return str(n)
    if n < 1_000_000:
        return f"{n / 1000:.1f}K"
    if n < 1_000_000_000:
        return f"{n / 1_000_000:.1f}M"
    return f"{n / 1_000_000_000:.1f}G"


def main() -> int:
    argparse.ArgumentParser(
        prog="claude-busy-monitor",
        description=(
            "List active Claude sessions for the current user with their state. "
            "Prints a state-summary line (busy / asking / idle counts) followed "
            "by one line per session with cumulative token totals. Output is "
            "suitable for `watch`."
        ),
    ).parse_args()

    sessions = get_sessions()
    state_counts = get_state_counts(sessions)

    print(" ".join(_colorize(f" {n} {state} ", state, n > 0) for state, n in state_counts.items()))
    print()
    for s in sessions:
        state_colored = _colorize(f" {s.state:^6} ", s.state)
        sid = s.id.split("-")[-1]
        if s.stats is not None:
            out_s = _humanize_count(s.stats.output)
            in_s = _humanize_count(s.stats.input)
            metrics = f"  out:{out_s:>6}  in:{in_s:>6}"
        else:
            metrics = ""
        print(f"{sid} {state_colored} {s.name:<28}{metrics}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
