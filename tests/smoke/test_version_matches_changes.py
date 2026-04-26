"""Smoke: `__version__` matches the topmost CHANGES.md heading.

Seed: #3 § 3.7 item 7. Regression target: a version bump in
`CHANGES.md` must propagate to `pyproject.toml` (via hatch regex)
and to `__version__` (via `importlib.metadata`) — drift breaks the
single-source-of-truth contract.
"""

import re
from pathlib import Path

from claude_busy_monitor import __version__


def test_version_matches_topmost_changes_heading():
    repo_root = Path(__file__).resolve().parents[2]
    changes_md = repo_root / "CHANGES.md"
    text = changes_md.read_text()
    match = re.search(r"^## Version (?P<v>\d+\.\d+\.\d+):", text, re.MULTILINE)
    assert match is not None, "CHANGES.md has no `## Version X.Y.Z:` heading"
    assert __version__ == match.group("v")
