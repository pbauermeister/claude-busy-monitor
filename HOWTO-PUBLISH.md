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
make publish                       # runs pre-flight, builds, uploads
unset UV_PUBLISH_TOKEN             # clear when done
```

**Durable path** (keyring, one-time setup):

```bash
uv tool install keyring
keyring set https://upload.pypi.org/legacy/ __token__   # paste token at prompt
echo 'export UV_KEYRING_PROVIDER=subprocess' >> ~/.bashrc
```

After this, `make publish` finds the token automatically — no env var needed.

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

## 3. Publish

1. **Bump `CHANGES.md`** — add `## Version X.Y.Z:` at the top with the changelog for this release. The version regex in `pyproject.toml` reads this single source of truth.
2. **Commit and push** the bump:

   ```bash
   git add CHANGES.md
   git commit -m "release: vX.Y.Z"
   git push origin main
   ```

3. **Run pre-flight** (optional — `make publish` does it too):

   ```bash
   make publish-preflight
   ```

4. **Publish**:

   ```bash
   make publish
   ```

   This runs the pre-flight, builds wheel + sdist into `dist/`, then `uv publish` uploads them.

## 4. Tag and push

Tag **only after** a successful upload — the tag is the durable record that PyPI accepted the artefact.

```bash
VERSION=$(awk -F'[ :]' '/^## Version / {print $3; exit}' CHANGES.md)
git tag "v$VERSION"
git push origin "v$VERSION"
```

If tagging is forgotten, the next `make publish-preflight` will not catch it (the version-already-on-PyPI case isn't checked) — but your next bump will overwrite the bug. So tag promptly.

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
- **`403 Forbidden` "filename has already been used"** — this exact wheel/sdist filename is already on PyPI (PyPI never lets you re-upload, even after deletion). Bump `CHANGES.md` and try again.
- **`make publish-preflight` says branch must be 'main' but you're on `main`** — `git rev-parse --abbrev-ref HEAD` reports something else (e.g. `HEAD` if detached). Run `git status` to see the actual state.
- **`uv publish` hangs uploading** — check network; `uv publish --verbose` shows progress.
- **Pre-flight passes but build fails** — `make build` runs `lint` first; a failing ruff check blocks publish. Fix the lint, commit (otherwise the next pre-flight rejects the dirty tree), retry.
