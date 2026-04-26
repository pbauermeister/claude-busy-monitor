"""Smoke: install-legacy → uninstall-legacy round-trip in an isolated venv.

Seed: #3 § 3.7 item 8. Regression target: the original `uninstall-legacy`
recipe used `uv pip uninstall || pip uninstall`, but `uv pip uninstall`
returns 0 when it has no record of the package, swallowing the fallback.
This test creates a fresh venv per run to avoid touching the user's
site-packages.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _venv_python(venv_dir: Path) -> Path:
    return venv_dir / "bin" / "python"


def _venv_pip(venv_dir: Path) -> Path:
    return venv_dir / "bin" / "pip"


@pytest.fixture(scope="module")
def isolated_venv(tmp_path_factory):
    venv_dir = tmp_path_factory.mktemp("smoke_venv") / "venv"
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)],
        check=True,
        capture_output=True,
    )
    return venv_dir


def test_install_legacy_roundtrip_makes_package_importable_then_not(isolated_venv):
    pip = str(_venv_pip(isolated_venv))
    py = str(_venv_python(isolated_venv))

    install = subprocess.run(
        [pip, "install", str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )
    assert install.returncode == 0, install.stderr

    importable = subprocess.run(
        [py, "-c", "import claude_busy_monitor; print(claude_busy_monitor.__version__)"],
        capture_output=True,
        text=True,
    )
    assert importable.returncode == 0, importable.stderr
    assert importable.stdout.strip()  # version string was printed

    uninstall = subprocess.run(
        [pip, "uninstall", "-y", "claude-busy-monitor"],
        capture_output=True,
        text=True,
    )
    assert uninstall.returncode == 0, uninstall.stderr

    not_importable = subprocess.run(
        [py, "-c", "import claude_busy_monitor"],
        capture_output=True,
        text=True,
    )
    assert not_importable.returncode != 0
    assert "ModuleNotFoundError" in not_importable.stderr
