"""Smoke test: package exposes its public API.

Stub for TODO #2 (test scaffold + testability discussion). This file
exists so `make test` (and `make cycle`) can succeed before the full
scaffold lands.
"""

import claude_busy_monitor


def test_package_exposes_public_api():
    assert claude_busy_monitor.__version__
    assert callable(claude_busy_monitor.get_sessions)
    assert callable(claude_busy_monitor.get_state_counts)
    assert hasattr(claude_busy_monitor, "ClaudeSession")
    assert hasattr(claude_busy_monitor, "ClaudeState")
    assert hasattr(claude_busy_monitor, "TokenStats")
