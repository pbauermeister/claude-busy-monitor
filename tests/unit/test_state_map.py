"""Unit tests: `_PROBE_STATUS_MAP` keys exactly match v2.1.119 status enum.

Seed: #3 § 3.7 item 5. Regression target: README §A4 — adding a fourth
`status` value without updating the map silently drops affected sessions.
"""

from claude_busy_monitor import ClaudeState
from claude_busy_monitor._sessions import _PROBE_STATUS_MAP


def test_state_map_has_exactly_three_keys():
    assert set(_PROBE_STATUS_MAP.keys()) == {"busy", "idle", "waiting"}


def test_state_map_busy_string_maps_to_BUSY_state():
    assert _PROBE_STATUS_MAP["busy"] == ClaudeState.BUSY


def test_state_map_idle_string_maps_to_IDLE_state():
    assert _PROBE_STATUS_MAP["idle"] == ClaudeState.IDLE


def test_state_map_waiting_string_maps_to_ASKING_state():
    assert _PROBE_STATUS_MAP["waiting"] == ClaudeState.ASKING
