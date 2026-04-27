#!/usr/bin/env bash
# Tag the current commit with v$VERSION extracted from CHANGES.md and push the
# tag to origin. Intended to be called AFTER a successful `make publish` so the
# tag exists iff PyPI accepted the artefact (pre-flight's tag-absent guard then
# blocks accidental re-publishing of the same version).
#
# Guards:
#   - CHANGES.md has a `## Version X.Y.Z[.postN]:` heading at the top.
#   - Tag `v$VERSION` does not exist locally.
#   - Tag `v$VERSION` does not exist on `origin` (network call).
#
# Env vars:
#   PUBLISH_ALLOW_RETAG — non-empty force-tags + force-pushes (with WARNING),
#     bypassing both tag-absent guards. Intended for fixing a botched tag,
#     not for normal use.
#
# Run from the repository root. Tested via the live publish rounds in #9.

set -eu

VERSION=$(awk -F'[ :]' '/^## Version / {print $3; exit}' CHANGES.md 2>/dev/null || true)
if [ -z "${VERSION:-}" ]; then
    echo "publish-tag: cannot extract version from CHANGES.md" >&2
    exit 1
fi

FORCE=""
if [ -n "${PUBLISH_ALLOW_RETAG:-}" ]; then
    FORCE="-f"
    echo "publish-tag: WARNING — retag bypass active (PUBLISH_ALLOW_RETAG set)" >&2
else
    if git rev-parse --verify --quiet "refs/tags/v$VERSION" >/dev/null; then
        echo "publish-tag: tag v$VERSION already exists locally (set PUBLISH_ALLOW_RETAG=1 to force)" >&2
        exit 1
    fi
    if git ls-remote --exit-code --tags origin "refs/tags/v$VERSION" >/dev/null 2>&1; then
        echo "publish-tag: tag v$VERSION already exists on origin (set PUBLISH_ALLOW_RETAG=1 to force)" >&2
        exit 1
    fi
fi

git tag $FORCE "v$VERSION"
git push $FORCE origin "v$VERSION"
echo "publish-tag: v$VERSION tagged + pushed"
