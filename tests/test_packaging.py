"""Tests for the packaging helpers.

These do not build an executable - that takes minutes and needs PyInstaller.
They check the pieces around it: the self test, the spec file and the
installer script.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PACKAGING = ROOT / "packaging"


class TestSelfTest:
    def test_selftest_passes(self, tmp_path):
        """The command the release workflow runs against a frozen build."""
        report = tmp_path / "report.txt"
        result = subprocess.run(
            [sys.executable, "-m", "storytobook", "--selftest", "--report", str(report)],
            capture_output=True,
            text=True,
            cwd=ROOT,
            env={**_env(), "PYTHONPATH": str(ROOT / "src")},
            timeout=300,
        )
        assert result.returncode == 0, result.stdout + result.stderr

        text = report.read_text("utf-8")
        assert "All checks passed." in text
        assert "export pdf" in text
        assert "export epub" in text
        assert "export html" in text
        assert "FAILED" not in text

    def test_version_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "storytobook", "--version"],
            capture_output=True,
            text=True,
            cwd=ROOT,
            env={**_env(), "PYTHONPATH": str(ROOT / "src")},
            timeout=120,
        )
        assert result.returncode == 0
        assert re.match(r"^\d+\.\d+\.\d+", result.stdout.strip())


def _env() -> dict:
    import os

    env = dict(os.environ)
    env.pop("STORYTOBOOK_HOME", None)
    return env


class TestSpecFile:
    def test_spec_exists(self):
        assert (PACKAGING / "storytobook.spec").exists()

    def test_spec_does_not_exclude_unittest(self):
        """fpdf2 imports unittest.mock, so excluding it breaks PDF export."""
        text = (PACKAGING / "storytobook.spec").read_text("utf-8")
        excludes = text.split("EXCLUDES = [", 1)[1].split("]", 1)[0]
        assert '"unittest"' not in excludes

    def test_spec_excludes_the_heavy_engines(self):
        text = (PACKAGING / "storytobook.spec").read_text("utf-8")
        for engine in ("torch", "diffusers", "transformers", "whisper"):
            assert f'"{engine}"' in text

    def test_launcher_exists(self):
        assert (PACKAGING / "launcher.py").exists()


class TestInstallerScript:
    def test_script_exists(self):
        assert (PACKAGING / "storytobook.iss").exists()

    def test_script_has_the_required_sections(self):
        text = (PACKAGING / "storytobook.iss").read_text("utf-8")
        for section in ("[Setup]", "[Files]", "[Icons]", "[Run]"):
            assert section in text

    def test_script_does_not_use_the_deprecated_architecture_flag(self):
        text = (PACKAGING / "storytobook.iss").read_text("utf-8")
        assert "ArchitecturesInstallIn64BitMode=x64compatible" in text


class TestIcon:
    def test_icon_generator_exists(self):
        assert (PACKAGING / "make_icon.py").exists()

    def test_icon_generator_produces_an_ico(self, tmp_path):
        pytest.importorskip("PIL")
        result = subprocess.run(
            [sys.executable, str(PACKAGING / "make_icon.py"), str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert (tmp_path / "StoryToBook.ico").exists()
        assert (tmp_path / "icon.png").exists()


class TestWorkflow:
    def test_release_workflow_exists(self):
        assert (ROOT / ".github" / "workflows" / "release.yml").exists()

    def test_release_workflow_covers_both_platforms(self):
        text = (ROOT / ".github" / "workflows" / "release.yml").read_text("utf-8")
        assert "windows-latest" in text
        assert "macos-" in text
        assert "--selftest" in text
