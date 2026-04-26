#!/usr/bin/env bash
# PostToolUse Edit hook.
# Emits a concern-level warning (does not block) if a devlog or charter
# file appears to be missing `- Author:` or `- Review:` metadata.  Catches
# the case where a newly-created section or file forgets the attestation
# block entirely.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/config.env"

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r .tool_input.file_path)

case "$FILE" in
    $HOOK_GLOB_DEVLOG|$HOOK_GLOB_CHARTER_UPPER|$HOOK_GLOB_CHARTER_LOWER)
        if ! grep -q "^$HOOK_MARKER_AUTHOR_PREFIX" "$FILE" \
            || ! grep -q "^$HOOK_MARKER_REVIEW_PREFIX" "$FILE"; then
            echo "CONCERN: $FILE is missing $HOOK_MARKER_AUTHOR_PREFIX or $HOOK_MARKER_REVIEW_PREFIX metadata."
        fi
        ;;
esac

exit 0
