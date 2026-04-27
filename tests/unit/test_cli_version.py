"""Unit: CLI `--version` exits 0 and prints `prog version` matching __version__.

Drives `claude_busy_monitor._cli.main` with `--version` via `argparse`'s
`action="version"`, which raises SystemExit(0) after writing to stdout.
"""

import sys

import pytest

from claude_busy_monitor import __version__
from claude_busy_monitor._cli import main


def test_version_flag_exits_zero_and_prints_version(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["claude-busy-monitor", "--version"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert __version__ in captured.out
    assert "claude-busy-monitor" in captured.out
