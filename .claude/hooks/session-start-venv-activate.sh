#!/usr/bin/env bash
# SessionStart hook (matcher: startup).
# Activates the project's Python venv and exports VIRTUAL_ENV + PATH into
# $CLAUDE_ENV_FILE so the venv survives for the whole session's Bash tool
# calls.  $CLAUDE_ENV_FILE is sourced after every Bash invocation; writing
# `export` lines into it lets the hook seed environment that persists across
# the session without a wrapper script per command.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/config.env"

REPO="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$REPO" ] && [ -f "$REPO/$HOOK_VENV_ACTIVATE_REL" ] || exit 0

# shellcheck disable=SC1091
source "$REPO/$HOOK_VENV_ACTIVATE_REL"

if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    printf 'export VIRTUAL_ENV=%q\n' "$VIRTUAL_ENV" >> "$CLAUDE_ENV_FILE"
    printf 'export PATH=%q\n' "$PATH" >> "$CLAUDE_ENV_FILE"
fi
exit 0
