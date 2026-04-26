"""Unit tests: `get_state_counts` always returns the full ClaudeState keyset.

Seed: #3 § 3.7 item 6.
"""

from claude_busy_monitor import ClaudeSession, ClaudeState, get_state_counts


def test_state_counts_empty_returns_all_three_keys_with_zero():
    counts = get_state_counts(sessions=[])
    assert counts == {
        ClaudeState.BUSY: 0,
        ClaudeState.ASKING: 0,
        ClaudeState.IDLE: 0,
    }


def test_state_counts_aggregates_mixed_sessions():
    sessions = [
        ClaudeSession(path="/a", name="a", id="1", state=ClaudeState.BUSY),
        ClaudeSession(path="/b", name="b", id="2", state=ClaudeState.BUSY),
        ClaudeSession(path="/c", name="c", id="3", state=ClaudeState.IDLE),
    ]
    counts = get_state_counts(sessions)
    assert counts == {
        ClaudeState.BUSY: 2,
        ClaudeState.ASKING: 0,
        ClaudeState.IDLE: 1,
    }


def test_state_counts_keeps_zero_keys_when_only_one_state_present():
    sessions = [
        ClaudeSession(path="/a", name="a", id="1", state=ClaudeState.ASKING),
    ]
    counts = get_state_counts(sessions)
    assert counts == {
        ClaudeState.BUSY: 0,
        ClaudeState.ASKING: 1,
        ClaudeState.IDLE: 0,
    }
