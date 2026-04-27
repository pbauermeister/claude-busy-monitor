"""Smoke: publish-preflight script rejects unsafe states and accepts clean state.

Drives `scripts/publish-preflight.sh` against synthetic git repos to exercise
each guard. The script itself runs in cwd, so each test sets up an isolated
tmp git repo and invokes the script there.
"""

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = REPO_ROOT / "scripts" / "publish-preflight.sh"


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=check,
    )


def _run_preflight(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(PREFLIGHT)],
        cwd=repo,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def clean_repo(tmp_path: Path) -> Path:
    """A fresh git repo on `main` with a committed CHANGES.md (version 0.1.0)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "CHANGES.md").write_text("# Changes\n\n## Version 0.1.0:\n\n- initial.\n")
    _git(repo, "add", "CHANGES.md")
    _git(repo, "commit", "-m", "initial")
    return repo


@pytest.fixture
def repo_with_origin(clean_repo: Path, tmp_path: Path) -> Path:
    """clean_repo with a bare `origin` remote, so `git ls-remote` works."""
    origin = tmp_path / "origin.git"
    _git(clean_repo, "init", "--bare", str(origin))
    _git(clean_repo, "remote", "add", "origin", str(origin))
    _git(clean_repo, "push", "origin", "main")
    return clean_repo


def test_preflight_passes_on_clean_repo(repo_with_origin: Path):
    result = _run_preflight(repo_with_origin)
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout
    assert "v0.1.0" in result.stdout


def test_preflight_rejects_missing_changes(clean_repo: Path):
    (clean_repo / "CHANGES.md").unlink()
    _git(clean_repo, "add", "-A")
    _git(clean_repo, "commit", "-m", "drop changes")
    result = _run_preflight(clean_repo)
    assert result.returncode != 0
    assert "cannot extract version" in result.stderr


def test_preflight_rejects_wrong_branch(repo_with_origin: Path):
    _git(repo_with_origin, "checkout", "-b", "feature")
    result = _run_preflight(repo_with_origin)
    assert result.returncode != 0
    assert "branch must be 'main'" in result.stderr
    assert "feature" in result.stderr


def test_preflight_rejects_modified_tree(repo_with_origin: Path):
    changes = repo_with_origin / "CHANGES.md"
    changes.write_text(changes.read_text() + "\nstray edit\n")
    result = _run_preflight(repo_with_origin)
    assert result.returncode != 0
    assert "not clean" in result.stderr


def test_preflight_rejects_untracked_file(repo_with_origin: Path):
    (repo_with_origin / "stray.txt").write_text("x\n")
    result = _run_preflight(repo_with_origin)
    assert result.returncode != 0
    assert "not clean" in result.stderr


def test_preflight_rejects_local_tag(repo_with_origin: Path):
    _git(repo_with_origin, "tag", "v0.1.0")
    result = _run_preflight(repo_with_origin)
    assert result.returncode != 0
    assert "exists locally" in result.stderr


def test_preflight_rejects_origin_tag(repo_with_origin: Path):
    _git(repo_with_origin, "tag", "v0.1.0")
    _git(repo_with_origin, "push", "origin", "v0.1.0")
    _git(repo_with_origin, "tag", "-d", "v0.1.0")  # remove local; origin still has it
    result = _run_preflight(repo_with_origin)
    assert result.returncode != 0
    assert "exists on origin" in result.stderr
