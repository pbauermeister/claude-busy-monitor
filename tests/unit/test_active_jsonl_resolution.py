"""Unit tests: `_find_active_jsonl` solo/multi disambiguation and path encoding.

Seeds: #3 § 3.7 items 2 (solo/multi) and 3 (path encoding).
"""

import time
from pathlib import Path

import pytest

from claude_busy_monitor._sessions import _find_active_jsonl


@pytest.fixture
def fake_projects_dir(tmp_path, monkeypatch):
    projects = tmp_path / "projects"
    projects.mkdir()
    monkeypatch.setattr("claude_busy_monitor._sessions.PROJECTS_DIR", projects)
    return projects


def _make_jsonl(directory: Path, sid: str) -> Path:
    path = directory / f"{sid}.jsonl"
    path.write_text("")
    return path


def test_active_jsonl_resolution_solo_returns_newest(fake_projects_dir):
    project = fake_projects_dir / "-home-user-project"
    project.mkdir()
    _make_jsonl(project, "old-session")
    time.sleep(0.01)
    newer = _make_jsonl(project, "new-session")
    result = _find_active_jsonl("/home/user/project", session_id_hint=None, solo=True)
    assert result == newer


def test_active_jsonl_resolution_multi_uses_session_id_hint(fake_projects_dir):
    project = fake_projects_dir / "-home-user-project"
    project.mkdir()
    _make_jsonl(project, "alpha-session")
    target = _make_jsonl(project, "beta-session")
    result = _find_active_jsonl("/home/user/project", session_id_hint="beta-session", solo=False)
    assert result == target


def test_active_jsonl_resolution_multi_without_hint_returns_none(fake_projects_dir):
    project = fake_projects_dir / "-home-user-project"
    project.mkdir()
    _make_jsonl(project, "any-session")
    result = _find_active_jsonl("/home/user/project", session_id_hint=None, solo=False)
    assert result is None


def test_active_jsonl_resolution_multi_skips_missing_hint(fake_projects_dir):
    project = fake_projects_dir / "-home-user-project"
    project.mkdir()
    _make_jsonl(project, "alpha-session")
    result = _find_active_jsonl("/home/user/project", session_id_hint="ghost", solo=False)
    assert result is None


def test_active_jsonl_resolution_encodes_simple_path(fake_projects_dir):
    project = fake_projects_dir / "-home-user-project"
    project.mkdir()
    target = _make_jsonl(project, "s")
    result = _find_active_jsonl("/home/user/project", session_id_hint=None, solo=True)
    assert result == target


def test_active_jsonl_resolution_encodes_trailing_slash_as_trailing_dash(
    fake_projects_dir,
):
    project = fake_projects_dir / "-home-user-project-"
    project.mkdir()
    target = _make_jsonl(project, "s")
    result = _find_active_jsonl("/home/user/project/", session_id_hint=None, solo=True)
    assert result == target


def test_active_jsonl_resolution_preserves_embedded_dashes(fake_projects_dir):
    project = fake_projects_dir / "-home-user-my-project"
    project.mkdir()
    target = _make_jsonl(project, "s")
    result = _find_active_jsonl("/home/user/my-project", session_id_hint=None, solo=True)
    assert result == target


def test_active_jsonl_resolution_returns_none_when_project_dir_missing(
    fake_projects_dir,
):
    result = _find_active_jsonl("/nonexistent/path", session_id_hint=None, solo=True)
    assert result is None
