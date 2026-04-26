#!/usr/bin/env python3
"""PreToolUse Edit hook — section-aware attestation check.

The devlog / charter convention splits a file into top-level `## N.`
sections, each carrying its own `- Review:` metadata.  This hook allows
an Edit that lands in a `- Review: pending` section even if another
section of the same file carries `- Review: user`.  An Edit that lands
in a `- Review: user` section still requires an anchored
`^- Review: pending$` marker in new_string (the file-level rule), acting
as an explicit reset of that section's attestation.

Fallbacks (conservative — prefer false blocks over false allows):
  * File has no `^## ` top-level headers → file-level rule.
  * old_string cannot be located in the file → file-level rule.
  * old_string spans multiple sections → require pending marker if any
    covered section is user-attested.
"""
from __future__ import annotations

import json
import re
import sys

from hook_config import CONFIG

PENDING_RE = re.compile(r"^" + re.escape(CONFIG["HOOK_MARKER_REVIEW_PENDING"]) + r"$", re.M)
SECTION_HEADER_RE = re.compile(r"^## ")
SECTION_REVIEW_RE = re.compile(r"^" + re.escape(CONFIG["HOOK_MARKER_REVIEW_PREFIX"]) + r" (\w+)")


def build_section_map(lines: list[str]) -> list[tuple[int, int, str]]:
    """Return [(start_line, end_line, review), ...] — 1-indexed inclusive.

    A section starts on a `## ` header and extends to the line before the
    next `## ` header (or end of file).  The section's review is the
    first `^- Review: <word>` line inside it, or "none" if absent.
    """
    sections: list[tuple[int, int, str]] = []
    cur_start: int | None = None
    cur_review: str | None = None
    for i, line in enumerate(lines, start=1):
        if SECTION_HEADER_RE.match(line):
            if cur_start is not None:
                sections.append((cur_start, i - 1, cur_review or "none"))
            cur_start = i
            cur_review = None
        elif cur_start is not None and cur_review is None:
            m = SECTION_REVIEW_RE.match(line)
            if m:
                cur_review = m.group(1)
    if cur_start is not None:
        sections.append((cur_start, len(lines), cur_review or "none"))
    return sections


def require_pending_or_block(file_path: str, new_string: str) -> int:
    if PENDING_RE.search(new_string):
        return 0
    user_marker = CONFIG["HOOK_MARKER_REVIEW_USER"]
    pending_marker = CONFIG["HOOK_MARKER_REVIEW_PENDING"]
    sys.stderr.write(
        f'BLOCKED: {file_path} contains "{user_marker}". Reset to '
        f'"{pending_marker}" before editing reviewed content.\n'
    )
    return 2


def main() -> int:
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {})
    file_path: str = tool_input.get("file_path", "")

    # Scope: devlog files + charter files.  Root CLAUDE.md and everything
    # else is out of scope.
    if file_path.endswith(CONFIG["HOOK_SUBSTR_CLAUDE_MD"]):
        return 0
    in_scope = (
        CONFIG["HOOK_SUBSTR_DEVLOG"] in file_path
        or CONFIG["HOOK_SUBSTR_CHARTER_UPPER"] in file_path
        or CONFIG["HOOK_SUBSTR_CHARTER_LOWER"] in file_path
    )
    if not in_scope:
        return 0

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return 0

    # Fast path: no user attestation in file → allow.
    if "\n" + CONFIG["HOOK_MARKER_REVIEW_USER"] not in "\n" + content:
        return 0

    old_string: str = tool_input.get("old_string", "")
    new_string: str = tool_input.get("new_string", "")

    lines = content.splitlines()
    sections = build_section_map(lines)

    # Fallback 1: no sections in file.
    if not sections:
        return require_pending_or_block(file_path, new_string)

    # Fallback 2: empty old_string (file-creation-style Edit) — can't locate.
    if not old_string:
        return require_pending_or_block(file_path, new_string)

    # Locate old_string in the file (first occurrence — Edit guarantees
    # uniqueness when it succeeds, so any match is canonical).
    idx = content.find(old_string)
    if idx < 0:
        return require_pending_or_block(file_path, new_string)

    # Convert char offset to 1-indexed line numbers.
    start_line = content.count("\n", 0, idx) + 1
    end_line = start_line + old_string.count("\n")

    # Does the matched span overlap any user-attested section?
    for sec_start, sec_end, sec_review in sections:
        if end_line >= sec_start and start_line <= sec_end and sec_review == "user":
            return require_pending_or_block(file_path, new_string)

    # Span is confined to pending (or unattested) sections → allow.
    return 0


if __name__ == "__main__":
    sys.exit(main())
