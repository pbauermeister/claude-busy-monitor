"""Shared hook configuration — single source of truth.

Reads `.claude/hooks/config.env` (a shell-sourceable KEY=VALUE file) so
shell hooks (via `source`) and Python hooks (via `CONFIG`) resolve the
same paths, patterns, markers, and limits.  Values are strings; callers
cast to int where needed.

Why hand-rolled parsing (not python-dotenv or similar): hooks run on
every tool call and must have no non-stdlib dependencies — adding one
would tie hook execution to the project's venv state, defeating the
purpose of tiny always-available enforcement.  The config.env schema is
also intentionally narrow (flat KEY="VALUE" with `#` comments, no
variable interpolation, no multiline), so the loader stays under 15
lines.  If the schema ever grows (interpolation, multiline, sections),
revisit this trade-off.
"""
from __future__ import annotations

from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "config.env"


def load() -> dict[str, str]:
    """Parse config.env into a plain dict.

    Skips empty lines and `#` comments.  Strips an outer pair of double
    quotes from values (matches the shell-source semantics where
    `X="abc"` yields `abc`).
    """
    values: dict[str, str] = {}
    for raw in CONFIG_PATH.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] == '"':
            val = val[1:-1]
        values[key.strip()] = val
    return values


CONFIG = load()
