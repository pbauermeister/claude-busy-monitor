#!/usr/bin/env bash
# PostToolUse Edit hook.
# Emits a concern-level warning (does not block) when a *.md file has
# trailing whitespace on any line, or does not end with a terminal
# newline.  Mirrors the Prettier rules documented in root CLAUDE.md
# "Markdown formatting".
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/config.env"

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r .tool_input.file_path)

case "$FILE" in
    $HOOK_GLOB_MARKDOWN)
        if [ -n "$(tail -c 1 "$FILE")" ]; then
            echo "CONCERN: $FILE does not end with a newline."
        fi
        if grep -qP "\s+$" "$FILE"; then
            echo "CONCERN: $FILE has trailing whitespace."
        fi
        ;;
esac

exit 0
