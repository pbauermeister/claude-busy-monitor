#!/usr/bin/env bash
# Pre-flight safety checks for `make publish`. Exits non-zero with a
# one-line cause if the current state is unsafe to publish.
#
# Checks (in order, cheapest first):
#   1. CHANGES.md has a `## Version X.Y.Z:` heading at the top.
#   2. Current branch is `main` (bypass: PUBLISH_ALLOW_ANY_BRANCH=1).
#   3. Working tree is clean (no modified, staged, or untracked files
#      per .gitignore — `git status --porcelain` is empty).
#   4. Tag `v$VERSION` does not exist locally.
#   5. Tag `v$VERSION` does not exist on `origin` (network call).
#
# Env vars:
#   PUBLISH_ALLOW_ANY_BRANCH — non-empty bypasses the branch check, with
#     a WARNING. Intended for testing the publish process itself (e.g.
#     during early publish-workflow iterations), not for normal use.
#
# Run from the repository root. Tested by tests/smoke/test_publish_preflight.py.

set -eu

VERSION=$(awk -F'[ :]' '/^## Version / {print $3; exit}' CHANGES.md 2>/dev/null || true)
if [ -z "${VERSION:-}" ]; then
    echo "publish-preflight: cannot extract version from CHANGES.md (expected '## Version X.Y.Z:' line)" >&2
    exit 1
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ]; then
    if [ -n "${PUBLISH_ALLOW_ANY_BRANCH:-}" ]; then
        echo "publish-preflight: WARNING — branch check bypassed (PUBLISH_ALLOW_ANY_BRANCH set, branch='$BRANCH')" >&2
    else
        echo "publish-preflight: branch must be 'main' (current: '$BRANCH')" >&2
        echo "publish-preflight: hint — set PUBLISH_ALLOW_ANY_BRANCH=1 to bypass (intended for publish-process testing, not normal use)" >&2
        exit 1
    fi
fi

if [ -n "$(git status --porcelain)" ]; then
    echo "publish-preflight: working tree is not clean (commit, stash, or .gitignore stray files)" >&2
    git status --short >&2
    exit 1
fi

if git rev-parse --verify --quiet "refs/tags/v$VERSION" >/dev/null; then
    echo "publish-preflight: tag v$VERSION already exists locally (bump version in CHANGES.md)" >&2
    exit 1
fi

if git ls-remote --exit-code --tags origin "refs/tags/v$VERSION" >/dev/null 2>&1; then
    echo "publish-preflight: tag v$VERSION already exists on origin (bump version in CHANGES.md)" >&2
    exit 1
fi

echo "publish-preflight: OK — ready to publish v$VERSION"
