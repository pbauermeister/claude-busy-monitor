#!/usr/bin/env bash
# PreToolUse Bash hook.
# Blocks `git commit` on the `main` branch when the staged changes contain
# any path NOT in the housekeeping whitelist (HOOK_RE_HOUSEKEEPING in
# config.env).
#
# Housekeeping (allowed on main): TODO.md, Makefile, LICENSE, CEREMONIES.md,
# MEMORY.md, any top-level dotfile/dotdir (.gitignore, .prettierrc, .vscode/,
# .claude/, .github/, etc.), and CLAUDE.md / HOWTO-*.md anywhere.
# Everything else (claude_busy_monitor.py, architecture/*, README*.md, etc.)
# requires a task branch.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/config.env"

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r .tool_input.command)

case "$CMD" in
    *"git commit"*) ;;
    *)              exit 0 ;;
esac

BRANCH=$(git branch --show-current 2>/dev/null || true)
[ "$BRANCH" = "main" ] || exit 0

NON_HOUSEKEEPING=$(
    git diff --cached --name-only 2>/dev/null \
        | grep -vE "$HOOK_RE_HOUSEKEEPING" \
        || true
)

if [ -n "$NON_HOUSEKEEPING" ]; then
    echo "BLOCKED: Task-related commit on main — switch to a task branch first." >&2
    echo "Non-housekeeping paths:" >&2
    echo "$NON_HOUSEKEEPING" | sed 's/^/  /' >&2
    exit 2
fi

exit 0
