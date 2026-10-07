"""Unit tests: `_find_active_jsonl` hint-first selection and path encoding.

Seeds: #3 § 3.7 items 2 and 3; #25 (hint-first replaces solo/multi).
"""

import os
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


def test_active_jsonl_resolution_hint_beats_newer_unrelated_transcript(fake_projects_dir):
    # Regression for #25: a backgrounded session's parked front-end touches
    # its transcript hourly; the bg job's own (older) transcript must win.
    project = fake_projects_dir / "-home-user-project"
    project.mkdir()
    target = _make_jsonl(project, "bg-session")
    parked = _make_jsonl(project, "parked-front-end")
    os.utime(parked, (time.time() + 3600, time.time() + 3600))
    result = _find_active_jsonl("/home/user/project", session_id_hint="bg-session")
    assert result == target


def test_active_jsonl_resolution_without_hint_returns_newest(fake_projects_dir):
    project = fake_projects_dir / "-home-user-project"
    project.mkdir()
    _make_jsonl(project, "old-session")
    time.sleep(0.01)
    newer = _make_jsonl(project, "new-session")
    result = _find_active_jsonl("/home/user/project", session_id_hint=None)
    assert result == newer


def test_active_jsonl_resolution_missing_hint_falls_back_to_newest(fake_projects_dir):
    # Fresh session whose transcript is not written yet: best guess is newest.
    project = fake_projects_dir / "-home-user-project"
    project.mkdir()
    only = _make_jsonl(project, "alpha-session")
    result = _find_active_jsonl("/home/user/project", session_id_hint="ghost")
    assert result == only


def test_active_jsonl_resolution_empty_project_dir_returns_none(fake_projects_dir):
    project = fake_projects_dir / "-home-user-project"
    project.mkdir()
    result = _find_active_jsonl("/home/user/project", session_id_hint="ghost")
    assert result is None


def test_active_jsonl_resolution_encodes_simple_path(fake_projects_dir):
    project = fake_projects_dir / "-home-user-project"
    project.mkdir()
    target = _make_jsonl(project, "s")
    result = _find_active_jsonl("/home/user/project", session_id_hint=None)
    assert result == target


def test_active_jsonl_resolution_encodes_trailing_slash_as_trailing_dash(
    fake_projects_dir,
):
    project = fake_projects_dir / "-home-user-project-"
    project.mkdir()
    target = _make_jsonl(project, "s")
    result = _find_active_jsonl("/home/user/project/", session_id_hint=None)
    assert result == target


def test_active_jsonl_resolution_preserves_embedded_dashes(fake_projects_dir):
    project = fake_projects_dir / "-home-user-my-project"
    project.mkdir()
    target = _make_jsonl(project, "s")
    result = _find_active_jsonl("/home/user/my-project", session_id_hint=None)
    assert result == target


def test_active_jsonl_resolution_returns_none_when_project_dir_missing(
    fake_projects_dir,
):
    result = _find_active_jsonl("/nonexistent/path", session_id_hint=None)
    assert result is None
