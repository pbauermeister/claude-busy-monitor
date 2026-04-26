#!/usr/bin/env bash
# PostToolUse Edit hook.
# Emits a concern-level warning (does not block) if a *CLAUDE.md file has
# grown to or past the 300-line limit declared in root CLAUDE.md's
# Context hygiene section.  The check also covers subdirectory
# CLAUDE.md files (e.g. architecture/devlog/CLAUDE.md) — they share the
# same budget rationale even if the soft limit was originally written
# for root.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/config.env"

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r .tool_input.file_path)

case "$FILE" in
    $HOOK_GLOB_CLAUDE_MD)
        LINES=$(wc -l < "$FILE")
        if [ "$LINES" -ge "$HOOK_LIMIT_CLAUDE_MD_LINES" ]; then
            echo "CONCERN: CLAUDE.md is $LINES lines (limit: $HOOK_LIMIT_CLAUDE_MD_LINES)."
        fi
        ;;
esac

exit 0
