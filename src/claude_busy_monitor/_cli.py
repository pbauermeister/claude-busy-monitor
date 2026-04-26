"""Command-line entrypoint for `claude-busy-monitor`.

Prints a state summary line followed by one line per Claude session.
ANSI palette is base-16 — `watch`-friendly.
"""

from claude_busy_monitor import ClaudeState, get_sessions, get_state_counts

_ANSI_RESET = "\x1b[0m"

_FG_BLACK = "\x1b[30m"
_FG_GREY = "\x1b[90m"

_BG_BLACK = "\x1b[40m"
_BG_RED = "\x1b[41m"
_BG_GREEN = "\x1b[42m"
_BG_YELLOW = "\x1b[43m"

_FX_BLINK = "\x1b[5m"

_STATE_STYLE: dict[ClaudeState, str] = {
    ClaudeState.BUSY: _FG_BLACK + _BG_RED,
    ClaudeState.ASKING: _FG_BLACK + _BG_YELLOW + _FX_BLINK,
    ClaudeState.IDLE: _FG_BLACK + _BG_GREEN,
}


def _colorize(text: str, state: ClaudeState, doit: bool = True) -> str:
    """Wrap `text` in the ANSI style defined for `state`."""
    if not doit:
        return f"{_BG_BLACK}{_FG_GREY}{text}{_ANSI_RESET}"
    return f"{_STATE_STYLE[state]}{text}{_ANSI_RESET}"


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
    sessions = get_sessions()
    state_counts = get_state_counts(sessions)

    print(
        " ".join(
            _colorize(f" {n} {state} ", state, n > 0)
            for state, n in state_counts.items()
        )
    )
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
