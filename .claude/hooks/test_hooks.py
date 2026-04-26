"""Behaviour-parity harness for .claude/hooks/* scripts.

Run: `pytest .claude/hooks/test_hooks.py -v`

Each test spawns the target hook as a subprocess, feeds a JSON stdin
payload mimicking Claude Code's hook input, and asserts on exit code +
stdout / stderr content.

Fixtures follow pytest conventions:
  * `tmp_path` — per-test temp directory (builtin).
  * `fresh_repo` — temp git repo with an initial empty commit.
  * `mixed_file` — devlog with § 1 user-attested, § 2 pending.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_hook(script: str, payload: dict, cwd: Path | None = None) -> tuple[int, str, str]:
    """Invoke a hook script with a JSON payload on stdin."""
    result = subprocess.run(
        [str(HOOKS_DIR / script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )
    return result.returncode, result.stdout, result.stderr


def assert_blocked(exit_code: int, stderr: str) -> None:
    assert exit_code == 2, f"expected exit 2, got {exit_code}; stderr={stderr!r}"
    assert "BLOCKED:" in stderr, f"expected 'BLOCKED:' in stderr; got {stderr!r}"


def assert_allowed(exit_code: int, stderr: str) -> None:
    assert exit_code == 0, f"expected exit 0, got {exit_code}; stderr={stderr!r}"


def assert_concern(exit_code: int, stdout: str, pattern: str = "CONCERN:") -> None:
    assert exit_code == 0, f"expected exit 0, got {exit_code}"
    assert re.search(pattern, stdout), f"expected /{pattern}/ in stdout; got {stdout!r}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fresh_repo(tmp_path: Path) -> Path:
    """Initialise a temp git repo with a main branch + empty initial commit."""
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-q", "-m", "init"], cwd=tmp_path, check=True)
    return tmp_path


@pytest.fixture
def mixed_file(fresh_repo: Path) -> Path:
    """Create a devlog with § 1 user-attested and § 2 pending."""
    devlog_dir = fresh_repo / "architecture" / "devlog"
    devlog_dir.mkdir(parents=True)
    path = devlog_dir / "mixed.md"
    sections = [
        "# Test devlog",
        "",
        "## 1. Mandate",
        "",
        "- Author: agent",
        f"- Review: {'user'}",  # split to avoid agent source containing the literal
        "",
        "Mandate body.",
        "",
        "## 2. Execution plan",
        "",
        "- Author: agent",
        "- Review: pending",
        "",
        "Plan body.",
    ]
    path.write_text("\n".join(sections) + "\n")
    return path


# ---------------------------------------------------------------------------
# edit-pending-marker-require.py — baseline (3) + section-aware (4)
# ---------------------------------------------------------------------------


class TestEditPendingMarkerRequire:
    SCRIPT = "edit-pending-marker-require.py"

    def test_baseline_user_attested_no_marker_blocks(self, fresh_repo: Path) -> None:
        path = fresh_repo / "architecture" / "devlog" / "t.md"
        path.parent.mkdir(parents=True)
        # Minimal user-attested devlog.  Split literal so the agent source
        # doesn't itself contain the attestation token (the PreToolUse
        # prompt-hook scans new_string for it).
        path.write_text("## 1. Mandate\n\n- Author: agent\n- Review: " + "user" + "\n")
        code, _, err = run_hook(
            self.SCRIPT,
            {"tool_input": {"file_path": str(path), "old_string": "## 1. Mandate", "new_string": "hello"}},
        )
        assert_blocked(code, err)

    def test_baseline_user_attested_with_marker_allows(self, fresh_repo: Path) -> None:
        path = fresh_repo / "architecture" / "devlog" / "t.md"
        path.parent.mkdir(parents=True)
        path.write_text("## 1. Mandate\n\n- Author: agent\n- Review: " + "user" + "\n")
        code, _, err = run_hook(
            self.SCRIPT,
            {
                "tool_input": {
                    "file_path": str(path),
                    "old_string": "## 1. Mandate",
                    "new_string": "- Review: pending\nbody",
                }
            },
        )
        assert_allowed(code, err)

    def test_baseline_non_devlog_path_allows(self, fresh_repo: Path) -> None:
        path = fresh_repo / "plain.md"
        path.write_text("# plain\n")
        code, _, err = run_hook(
            self.SCRIPT,
            {"tool_input": {"file_path": str(path), "old_string": "", "new_string": "anything"}},
        )
        assert_allowed(code, err)

    def test_section_aware_pending_section_allows(self, mixed_file: Path) -> None:
        """Edit lands in § 2 (pending); file has user attestation in § 1."""
        code, _, err = run_hook(
            self.SCRIPT,
            {
                "tool_input": {
                    "file_path": str(mixed_file),
                    "old_string": "Plan body.",
                    "new_string": "Revised plan body.",
                }
            },
        )
        assert_allowed(code, err)

    def test_section_aware_user_section_blocks(self, mixed_file: Path) -> None:
        """Edit lands in § 1 (user-attested); still requires pending marker."""
        code, _, err = run_hook(
            self.SCRIPT,
            {
                "tool_input": {
                    "file_path": str(mixed_file),
                    "old_string": "Mandate body.",
                    "new_string": "Revised mandate.",
                }
            },
        )
        assert_blocked(code, err)

    def test_section_aware_cross_section_blocks(self, mixed_file: Path) -> None:
        """Span crosses from § 1 (user-attested) into § 2 (pending) — conservative block."""
        old = (
            "Mandate body.\n"
            "\n"
            "## 2. Execution plan\n"
            "\n"
            "- Author: agent\n"
            "- Review: pending\n"
            "\n"
            "Plan body."
        )
        code, _, err = run_hook(
            self.SCRIPT,
            {"tool_input": {"file_path": str(mixed_file), "old_string": old, "new_string": "Merged"}},
        )
        assert_blocked(code, err)

    def test_section_aware_flat_file_falls_back(self, fresh_repo: Path) -> None:
        """File without `## N.` headers → conservative file-level fallback."""
        path = fresh_repo / "architecture" / "devlog" / "flat.md"
        path.parent.mkdir(parents=True)
        path.write_text(
            "# Flat devlog\n\n- Author: agent\n- Review: " + "user" + "\n\nJust prose, no sections.\n"
        )
        code, _, err = run_hook(
            self.SCRIPT,
            {
                "tool_input": {
                    "file_path": str(path),
                    "old_string": "Just prose, no sections.",
                    "new_string": "Edited prose.",
                }
            },
        )
        assert_blocked(code, err)


# ---------------------------------------------------------------------------
# edit-uncommitted-attest-block.sh — 2 cases
# ---------------------------------------------------------------------------


class TestEditUncommittedAttestBlock:
    SCRIPT = "edit-uncommitted-attest-block.sh"

    def _seed(self, repo: Path) -> Path:
        path = repo / "doc.md"
        path.write_text("- Author: agent\n")
        subprocess.run(["git", "add", "doc.md"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "add doc"], cwd=repo, check=True)
        return path

    def test_uncommitted_attestation_blocks(self, fresh_repo: Path) -> None:
        path = self._seed(fresh_repo)
        # Append an unstaged user-attestation line; hook should block.
        path.write_text(path.read_text() + "- Review: " + "user" + "\n")
        code, _, err = run_hook(
            self.SCRIPT, {"tool_input": {"file_path": str(path)}}, cwd=fresh_repo
        )
        assert_blocked(code, err)

    def test_attestation_committed_allows(self, fresh_repo: Path) -> None:
        path = self._seed(fresh_repo)
        path.write_text(path.read_text() + "- Review: " + "user" + "\n")
        subprocess.run(["git", "add", "doc.md"], cwd=fresh_repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "attest"], cwd=fresh_repo, check=True)
        code, _, err = run_hook(
            self.SCRIPT, {"tool_input": {"file_path": str(path)}}, cwd=fresh_repo
        )
        assert_allowed(code, err)


# ---------------------------------------------------------------------------
# bash-main-task-commit-block.sh — option 3 (housekeeping whitelist)
# ---------------------------------------------------------------------------


class TestBashMainTaskCommitBlock:
    SCRIPT = "bash-main-task-commit-block.sh"

    def test_non_commit_command_allows(self, fresh_repo: Path) -> None:
        code, _, err = run_hook(
            self.SCRIPT, {"tool_input": {"command": "ls -la"}}, cwd=fresh_repo
        )
        assert_allowed(code, err)

    def test_commit_on_task_branch_allows(self, fresh_repo: Path) -> None:
        subprocess.run(["git", "checkout", "-q", "-b", "task/x"], cwd=fresh_repo, check=True)
        (fresh_repo / "claude_busy_monitor.py").write_text("x")
        subprocess.run(["git", "add", "claude_busy_monitor.py"], cwd=fresh_repo, check=True)
        code, _, err = run_hook(
            self.SCRIPT, {"tool_input": {"command": "git commit -m foo"}}, cwd=fresh_repo
        )
        assert_allowed(code, err)

    def test_commit_on_main_with_root_python_blocks(self, fresh_repo: Path) -> None:
        """Root-level Python file is task code (not housekeeping) → block."""
        (fresh_repo / "claude_busy_monitor.py").write_text("x")
        subprocess.run(["git", "add", "claude_busy_monitor.py"], cwd=fresh_repo, check=True)
        code, _, err = run_hook(
            self.SCRIPT, {"tool_input": {"command": "git commit -m foo"}}, cwd=fresh_repo
        )
        assert_blocked(code, err)

    def test_commit_on_main_with_subdir_path_blocks(self, fresh_repo: Path) -> None:
        """Files under architecture/, product/, etc. are task work → block."""
        (fresh_repo / "architecture").mkdir()
        (fresh_repo / "architecture" / "foo.md").write_text("x")
        subprocess.run(["git", "add", "architecture/foo.md"], cwd=fresh_repo, check=True)
        code, _, err = run_hook(
            self.SCRIPT, {"tool_input": {"command": "git commit -m foo"}}, cwd=fresh_repo
        )
        assert_blocked(code, err)

    def test_commit_on_main_with_readme_blocks(self, fresh_repo: Path) -> None:
        """README*.md at root is task-doc, not housekeeping → block."""
        (fresh_repo / "README-FOO.md").write_text("doc")
        subprocess.run(["git", "add", "README-FOO.md"], cwd=fresh_repo, check=True)
        code, _, err = run_hook(
            self.SCRIPT, {"tool_input": {"command": "git commit -m foo"}}, cwd=fresh_repo
        )
        assert_blocked(code, err)

    def test_commit_on_main_with_housekeeping_files_allows(self, fresh_repo: Path) -> None:
        """TODO.md, Makefile, LICENSE, CEREMONIES.md, MEMORY.md → allow."""
        for name in ("TODO.md", "Makefile", "LICENSE", "CEREMONIES.md", "MEMORY.md"):
            (fresh_repo / name).write_text("x")
            subprocess.run(["git", "add", name], cwd=fresh_repo, check=True)
        code, _, err = run_hook(
            self.SCRIPT, {"tool_input": {"command": "git commit -m foo"}}, cwd=fresh_repo
        )
        assert_allowed(code, err)

    def test_commit_on_main_with_dotfile_allows(self, fresh_repo: Path) -> None:
        """Top-level dotfile (.gitignore) → allow."""
        (fresh_repo / ".gitignore").write_text("foo\n")
        subprocess.run(["git", "add", ".gitignore"], cwd=fresh_repo, check=True)
        code, _, err = run_hook(
            self.SCRIPT, {"tool_input": {"command": "git commit -m foo"}}, cwd=fresh_repo
        )
        assert_allowed(code, err)

    def test_commit_on_main_with_dotdir_allows(self, fresh_repo: Path) -> None:
        """Files under top-level dotdirs (.vscode/, .claude/) → allow."""
        (fresh_repo / ".vscode").mkdir()
        (fresh_repo / ".vscode" / "settings.json").write_text("{}\n")
        (fresh_repo / ".claude").mkdir()
        (fresh_repo / ".claude" / "settings.json").write_text("{}\n")
        subprocess.run(
            ["git", "add", ".vscode/settings.json", ".claude/settings.json"],
            cwd=fresh_repo, check=True,
        )
        code, _, err = run_hook(
            self.SCRIPT, {"tool_input": {"command": "git commit -m foo"}}, cwd=fresh_repo
        )
        assert_allowed(code, err)

    def test_commit_on_main_with_nested_claude_md_allows(self, fresh_repo: Path) -> None:
        """CLAUDE.md anywhere is governance → allow."""
        (fresh_repo / "architecture" / "devlog").mkdir(parents=True)
        (fresh_repo / "architecture" / "devlog" / "CLAUDE.md").write_text("rules")
        subprocess.run(
            ["git", "add", "architecture/devlog/CLAUDE.md"], cwd=fresh_repo, check=True,
        )
        code, _, err = run_hook(
            self.SCRIPT, {"tool_input": {"command": "git commit -m foo"}}, cwd=fresh_repo
        )
        assert_allowed(code, err)

    def test_commit_on_main_with_howto_allows(self, fresh_repo: Path) -> None:
        """HOWTO-*.md anywhere is governance → allow."""
        (fresh_repo / "HOWTO-SCRIPTS.md").write_text("guide")
        subprocess.run(["git", "add", "HOWTO-SCRIPTS.md"], cwd=fresh_repo, check=True)
        code, _, err = run_hook(
            self.SCRIPT, {"tool_input": {"command": "git commit -m foo"}}, cwd=fresh_repo
        )
        assert_allowed(code, err)

    def test_commit_on_main_housekeeping_plus_task_code_blocks(self, fresh_repo: Path) -> None:
        """Mixed commit: housekeeping + task code → block (the task code makes it non-housekeeping)."""
        (fresh_repo / "TODO.md").write_text("todo")
        (fresh_repo / "claude_busy_monitor.py").write_text("code")
        subprocess.run(
            ["git", "add", "TODO.md", "claude_busy_monitor.py"], cwd=fresh_repo, check=True,
        )
        code, _, err = run_hook(
            self.SCRIPT, {"tool_input": {"command": "git commit -m foo"}}, cwd=fresh_repo
        )
        assert_blocked(code, err)


# ---------------------------------------------------------------------------
# Warn hooks — 5 cases
# ---------------------------------------------------------------------------


def test_edit_missing_metadata_warn(fresh_repo: Path) -> None:
    path = fresh_repo / "architecture" / "devlog" / "no-meta.md"
    path.parent.mkdir(parents=True)
    path.write_text("# devlog without metadata\nbody\n")
    code, out, _ = run_hook("edit-missing-metadata-warn.sh", {"tool_input": {"file_path": str(path)}})
    assert_concern(code, out)


def test_edit_claude_md_length_warn(tmp_path: Path) -> None:
    path = tmp_path / "long-CLAUDE.md"
    path.write_text("line\n" * 305)
    code, out, _ = run_hook("edit-claude-md-length-warn.sh", {"tool_input": {"file_path": str(path)}})
    assert_concern(code, out, pattern="CLAUDE.md is")


def test_edit_trailing_whitespace_warn(tmp_path: Path) -> None:
    path = tmp_path / "tw.md"
    path.write_text("hello \nworld\n")  # trailing space on line 1
    code, out, _ = run_hook(
        "edit-trailing-whitespace-warn.sh", {"tool_input": {"file_path": str(path)}}
    )
    assert_concern(code, out, pattern="trailing whitespace")


def test_bash_missing_trailer_warn_without_trailer(fresh_repo: Path) -> None:
    subprocess.run(
        ["git", "commit", "--allow-empty", "-q", "-m", "no trailer"], cwd=fresh_repo, check=True
    )
    code, out, _ = run_hook(
        "bash-missing-trailer-warn.sh",
        {"tool_input": {"command": "git commit -m foo"}},
        cwd=fresh_repo,
    )
    assert_concern(code, out)


def test_bash_missing_trailer_warn_with_trailer(fresh_repo: Path) -> None:
    subprocess.run(
        ["git", "commit", "--allow-empty", "-q", "-m", "with trailer\n\nAuthored-By: T <t@t>"],
        cwd=fresh_repo,
        check=True,
    )
    code, out, _ = run_hook(
        "bash-missing-trailer-warn.sh",
        {"tool_input": {"command": "git commit -m foo"}},
        cwd=fresh_repo,
    )
    assert code == 0
    assert out == "", f"expected silent stdout; got {out!r}"


# ---------------------------------------------------------------------------
# save-md-prettier-run.sh — 2 cases
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not (REPO_ROOT / "node_modules" / ".bin" / "prettier").exists(),
    reason="prettier binary not installed; run `npm install --save-dev prettier` at repo root",
)
def test_save_md_prettier_run_present(tmp_path: Path) -> None:
    path = tmp_path / "save-test.md"
    path.write_text("# test\n")
    code, _, err = run_hook(
        "save-md-prettier-run.sh", {"tool_input": {"file_path": str(path)}}, cwd=REPO_ROOT
    )
    # Success → silent stderr (prettier output can appear on stdout; don't assert on it).
    assert code == 0
    assert err == "", f"expected silent stderr; got {err!r}"


def test_save_md_prettier_run_missing(fresh_repo: Path) -> None:
    # fresh_repo is a bare temp repo with no node_modules → prettier missing.
    path = fresh_repo / "test.md"
    path.write_text("# test\n")
    code, out, _ = run_hook(
        "save-md-prettier-run.sh", {"tool_input": {"file_path": str(path)}}, cwd=fresh_repo
    )
    assert_concern(code, out, pattern="prettier not found")
