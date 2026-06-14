"""Unit tests: `_PROBE_STATUS_MAP` keys exactly match the claude status enum.

Seed: #3 § 3.7 item 5. Regression target: README §A4 — adding a new
`status` value without updating the map silently drops affected sessions.
The `"shell"` key (#21) is the lived instance of that failure mode.
"""

from claude_busy_monitor import ClaudeState
from claude_busy_monitor._sessions import _PROBE_STATUS_MAP


def test_state_map_has_exactly_four_keys():
    assert set(_PROBE_STATUS_MAP.keys()) == {"busy", "shell", "idle", "waiting"}


def test_state_map_busy_string_maps_to_BUSY_state():
    assert _PROBE_STATUS_MAP["busy"] == ClaudeState.BUSY


def test_state_map_idle_string_maps_to_IDLE_state():
    assert _PROBE_STATUS_MAP["idle"] == ClaudeState.IDLE


def test_state_map_shell_string_maps_to_BUSY_state():
    # A shelled-out session looks active to the user (#21). README §A4.
    assert _PROBE_STATUS_MAP["shell"] == ClaudeState.BUSY


def test_state_map_waiting_string_maps_to_ASKING_state():
    assert _PROBE_STATUS_MAP["waiting"] == ClaudeState.ASKING
