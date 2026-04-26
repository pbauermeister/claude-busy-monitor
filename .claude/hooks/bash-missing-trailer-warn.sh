#!/usr/bin/env bash
# PostToolUse Bash hook.
# After a Bash tool call containing `git commit`, inspects the most
# recent commit message and emits a concern-level warning (does not
# block) if it lacks an `Authored-By:` or `Co-Authored-By:` trailer.
# See root CLAUDE.md "Git commit trailers" table.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/config.env"

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r .tool_input.command)

case "$CMD" in
    *"git commit"*)
        MSG=$(git log -1 --format=%B 2>/dev/null || true)
        if ! echo "$MSG" | grep -qE "$HOOK_RE_COAUTHOR_TRAILER"; then
            echo "CONCERN: commit is missing Authored-By or Co-Authored-By trailer."
        fi
        ;;
esac

exit 0
