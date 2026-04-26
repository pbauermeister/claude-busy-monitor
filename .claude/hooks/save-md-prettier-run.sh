#!/usr/bin/env bash
# PostToolUse Edit + Write hook (shared).
# Runs `prettier --write` on `*.md` files after they are saved.  Uses the
# prettier binary vendored under node_modules/ at the repo root so no
# global install is required.  Emits a concern-level warning if prettier
# is missing, otherwise silent on success.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/config.env"

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r .tool_input.file_path)

case "$FILE" in
    $HOOK_GLOB_MARKDOWN)
        ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
        [ -n "$ROOT" ] || exit 0
        PRETTIER="$ROOT/$HOOK_PRETTIER_REL"
        if [ ! -x "$PRETTIER" ]; then
            echo "CONCERN: prettier not found at $PRETTIER — *.md files are not being auto-formatted. Install with 'npm install --save-dev prettier' at the repo root."
            exit 0
        fi
        "$PRETTIER" --write "$FILE" 2>/dev/null || true
        ;;
esac

exit 0
