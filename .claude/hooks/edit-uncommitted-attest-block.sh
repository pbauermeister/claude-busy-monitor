#!/usr/bin/env bash
# PreToolUse Edit hook.
# Blocks the edit if the target file's working-tree diff contains an
# uncommitted addition of "- Review: user".  Reason: user attestations
# must be committed before the agent edits the file, so the commit
# boundary cleanly separates pre-attestation and post-attestation state.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/config.env"

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r .tool_input.file_path)

[ -f "$FILE" ] || exit 0

if git diff -- "$FILE" | grep -q "^+$HOOK_MARKER_REVIEW_USER"; then
    echo "BLOCKED: $FILE has an uncommitted addition of \"$HOOK_MARKER_REVIEW_USER\". The user attestation must be committed before the agent edits this file." >&2
    exit 2
fi

exit 0
