# How to publish to PyPI

End-to-end procedure for releasing a new version of `claude-busy-monitor` to PyPI.
The publish itself is **maintainer-only**; the workflow below assumes you have push access to `origin/main` and a PyPI account.

## 1. Prerequisites

- **PyPI account** at https://pypi.org/.
- **API token**: create one at https://pypi.org/manage/account/token/.
  - First publish: account-scoped (no project to scope to yet).
  - After first publish: rotate to a **project-scoped** token (`Scope: Project — claude-busy-monitor`) so a leak can only damage this package.
  - Token format: `pypi-AgEI...` (~180 chars). Keep it secret.
- **`uv`** ≥ 0.11 (this repo's `Makefile` invokes `uv publish`). `make require` installs it if missing.

### 1.1 Hold the token

`uv publish` reads credentials from these sources (in priority order):

| Source                                     | Persistence     | When to use                                                                        |
| ------------------------------------------ | --------------- | ---------------------------------------------------------------------------------- |
| `UV_PUBLISH_TOKEN` env var                 | per-shell       | **Default for interactive use.** Paste before each publish session.                |
| Keyring (`UV_KEYRING_PROVIDER=subprocess`) | durable, secure | If you publish often. Requires `keyring` CLI + one-time `keyring set` (see below). |
| `-t/--token` CLI flag                      | one-shot        | Avoid — leaks into shell history.                                                  |
| OIDC trusted publishing                    | CI-only         | GitHub Actions etc. Not relevant for manual local publish.                         |
| `~/.pypirc`                                | **not used**    | That's `twine`'s config; `uv publish` does **not** read it.                        |

**Default path** (env var, no install):

```bash
read -s UV_PUBLISH_TOKEN          # paste token; -s hides it from the terminal
export UV_PUBLISH_TOKEN
make publish                       # uploads dist/* via uv publish
unset UV_PUBLISH_TOKEN             # clear when done
```

**Durable path** (keyring, one-time setup):

```bash
uv tool install keyring
keyring set https://upload.pypi.org/legacy/ __token__   # paste token at prompt
cat >> ~/.bashrc <<'EOF'
export UV_KEYRING_PROVIDER=subprocess
export UV_PUBLISH_USERNAME=__token__
EOF
```

Both env vars are required: `UV_KEYRING_PROVIDER=subprocess` tells uv to consult keyring, and `UV_PUBLISH_USERNAME=__token__` tells it which key to look up. Without the username, uv has no key to query and falls back to interactive prompts (then 403s if the prompt input is incomplete). After this one-time setup, `make publish` finds the token automatically.

**For the very first publish on a new account**: the token MUST be **account-scoped** (`Scope: Entire account`), not project-scoped — PyPI auto-creates the project (`claude-busy-monitor`) on the first successful upload, so a project-scoped token has nothing to scope to yet. Rotate to a project-scoped token after the first publish for tighter blast radius.

## 2. Pre-flight

`make publish-preflight` runs five guards (also run automatically by `make publish`):

| Guard                                         | Failure means…                                          | Fix                                                 |
| --------------------------------------------- | ------------------------------------------------------- | --------------------------------------------------- |
| `CHANGES.md` has `## Version X.Y.Z:` heading  | Version source-of-truth is broken.                      | Add the heading at the top of `CHANGES.md`.         |
| Branch is `main`                              | You're on a feature branch.                             | `git checkout main` first.                          |
| Working tree clean (`git status --porcelain`) | Modified, staged, or untracked files would be excluded. | Commit, stash, or `.gitignore` the stray file.      |
| Tag `vX.Y.Z` not present locally              | This version was already tagged.                        | Bump `CHANGES.md` to the next `0.x.y` (or `x.y.z`). |
| Tag `vX.Y.Z` not present on `origin`          | This version was already published from another clone.  | Bump `CHANGES.md`.                                  |

The last guard makes a network call (`git ls-remote`); the rest are local. All run before `uv publish`, so a rejection costs no network traffic to PyPI.

### 2.1 Bypass: testing the publish process from a feature branch

Setting `PUBLISH_ALLOW_ANY_BRANCH=1` skips the branch check (with a `WARNING` line) so you can rehearse `make publish-quality` and `make publish` from a non-`main` branch. Intended for testing the publish workflow itself (e.g. iterating on `0.1.x` bumps to validate this very pipeline), **not** for normal releases — production releases must happen from `main` so the published artefact is reproducible from `git checkout v$VERSION`.

```bash
PUBLISH_ALLOW_ANY_BRANCH=1 make publish-quality
PUBLISH_ALLOW_ANY_BRANCH=1 make publish
```

The other four pre-flight guards still run; only the branch identity is waived.

## 3. Publish

1. **Bump `CHANGES.md`** — add `## Version X.Y.Z:` at the top with the changelog for this release. The version regex in `pyproject.toml` reads this single source of truth.

   **Version convention**:
   - `X.Y.Z` — anything that goes into the wheel and changes user-visible state (code, README content, public docs).
   - `X.Y.Z.postN` — PEP 440 post-release; **reserved for publishing-mechanism fixes only** (same wheel content re-uploaded with corrected metadata, e.g. README rendering broken on PyPI). Code changes never warrant a `.postN`.

2. **Commit and push** the bump:

   ```bash
   git add CHANGES.md
   git commit -m "release: vX.Y.Z"
   git push origin main
   ```

3. **Run the pre-publish gate** (recommended):

   ```bash
   make publish-quality
   ```

   `publish-quality` runs `lint` → unit + smoke tests → `build` → `uninstall` → `verify-uninstalled` → `clean` → `install` → `verify-installed` → `publish-preflight`. Halts on the first failure; does **not** upload. If you only want the pre-flight checks (no install round-trip), use `make publish-preflight` standalone.

4. **Publish**:

   ```bash
   make publish
   ```

   `make publish` is a raw `uv publish` — it assumes `publish-quality` was run first.

## 4. Tag

Tag **only after** a successful upload — the tag is the durable record that PyPI accepted the artefact, and `publish-preflight` then rejects accidental re-publishing of the same version.

```bash
make publish-tag
```

`publish-tag` extracts the version from `CHANGES.md`, guards on tag-absent (local + origin), then `git tag v$VERSION && git push origin v$VERSION`. Use `PUBLISH_ALLOW_RETAG=1` to force-retag if you need to fix a botched tag.

## 5. Verify

In a fresh shell, install from PyPI into a throwaway venv and confirm the CLI works:

```bash
cd /tmp
python3 -m venv verify-venv
source verify-venv/bin/activate
pip install claude-busy-monitor=="$VERSION"
claude-busy-monitor --help     # should print usage
deactivate
rm -rf verify-venv
```

If `pip install` resolves an older version, PyPI hasn't propagated the new release yet (usually <60 s). Retry.

## 6. Troubleshooting

- **`401 Unauthorized` from `uv publish`** — token is wrong, expired, or not scoped to this project. Regenerate at https://pypi.org/manage/account/token/.
- **`403 Forbidden` "Invalid or non-existent authentication information"** — token rejected by PyPI. Most common causes: (a) project-scoped token used for the first-ever upload (project doesn't exist yet — use account-scoped for the first round); (b) TestPyPI token used against PyPI; (c) malformed token (whitespace, missing `pypi-` prefix).
- **`403 Forbidden` "filename has already been used"** — this exact wheel/sdist filename is already on PyPI (PyPI never lets you re-upload, even after deletion). Bump `CHANGES.md` and try again.
- **`uv publish` prompts for username/password despite keyring being set** — `UV_KEYRING_PROVIDER=subprocess` alone is not enough; uv also needs `UV_PUBLISH_USERNAME=__token__` to know what to look up. Set both env vars (see § 1.1).
- **`make publish-preflight` says branch must be 'main' but you're on `main`** — `git rev-parse --abbrev-ref HEAD` reports something else (e.g. `HEAD` if detached). Run `git status` to see the actual state.
- **`uv publish` hangs uploading** — check network; `uv publish --verbose` shows progress.
- **`make publish` fails with "No files found to publish"** — `dist/` is empty. `make publish-quality` rebuilds `dist/` as its last step; run it before `make publish`. Standalone fix: `make build`.
