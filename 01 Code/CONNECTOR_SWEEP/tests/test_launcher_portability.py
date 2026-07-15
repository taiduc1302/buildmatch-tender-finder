from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
LAUNCHER = PACKAGE_ROOT / "Launch_TENDER_FINDER_GUI.bat"
SETUP = PACKAGE_ROOT / "setup_tenderfinder_environment.bat"
BOOTSTRAP = PACKAGE_ROOT / "_python_bootstrap.bat"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_canonical_launcher_is_repo_relative_and_setup_cannot_rewrite_it() -> None:
    launcher_text = LAUNCHER.read_text(encoding="utf-8", errors="replace")
    setup_text = SETUP.read_text(encoding="utf-8", errors="replace")
    assert "%~dp0" in launcher_text
    assert ".venv\\Scripts\\pythonw.exe" in launcher_text
    assert "setup_tenderfinder_environment.bat" in launcher_text
    assert "C:\\Projects\\buildmatch-tender-finder" not in launcher_text
    assert '> "%ROOT_LAUNCHER%"' not in setup_text
    assert '>> "%ROOT_LAUNCHER%"' not in setup_text
    assert "[Environment]::GetFolderPath('Desktop')" in setup_text
    assert "call :CREATE_DESKTOP_SHORTCUT" in setup_text
    assert "$link.TargetPath=$env:TENDER_FINDER_SHORTCUT_TARGET" in setup_text
    assert "WScript.CreateObject" not in setup_text
    assert 'call "%ROOT_LAUNCHER%"' in setup_text
    assert "Canonical launcher preserved" in setup_text


def test_setup_propagates_dependency_failures_and_uses_canonical_requirements() -> None:
    setup_text = SETUP.read_text(encoding="utf-8", errors="replace")
    launcher_text = LAUNCHER.read_text(encoding="utf-8", errors="replace")
    assert 'set "REQUIREMENTS=%ROOT%requirements.txt"' in setup_text
    assert "pip install -r" in setup_text
    assert "ERROR: pip install failed" in setup_text
    assert "ERROR: Playwright Chromium installation failed" in setup_text
    assert "exit /b 1" in setup_text
    for dependency in (
        "openpyxl", "bs4", "playwright", "pandas", "pdfplumber",
        "requests", "yaml", "regex",
    ):
        assert dependency in launcher_text
    assert "required Python dependencies still cannot be imported" in launcher_text


def test_python_bootstrap_requires_supported_python_and_is_actionable() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8", errors="replace")
    assert "sys.version_info.major == 3" in text
    assert "range(0,11)" in text
    assert "TENDER_FINDER needs Python 3.11 or newer" in text
    assert "https://www.python.org/downloads/" in text
    assert "exit /b 1" in text


def test_python_bootstrap_preserves_supported_path_precedence_on_windows() -> None:
    if os.name != "nt":
        print("[SKIP] Windows-only bootstrap precedence execution")
        return
    with tempfile.TemporaryDirectory(prefix="tenderfinder_fake_python_") as temp:
        fake = Path(temp) / "python.cmd"
        fake.write_text(
            "@echo off\n"
            "if \"%~1\"==\"-c\" exit /b 0\n"
            "if \"%~1\"==\"--version\" echo Python 3.12.0\n"
            "exit /b 0\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        system_root = Path(env.get("SystemRoot", r"C:\Windows"))
        env["PATH"] = str(Path(temp)) + os.pathsep + str(system_root / "System32")
        env["TENDER_FINDER_BOOTSTRAP_INSTALL_ATTEMPTED"] = "1"
        env["TENDER_FINDER_BOOTSTRAP_BROWSER_OPENED"] = "1"
        wrapper = Path(temp) / "run_bootstrap.cmd"
        wrapper.write_text(
            "@echo off\n"
            f'call "{BOOTSTRAP}"\n'
            "set \"RC=%errorlevel%\"\n"
            "echo RESULT=%PY_LAUNCHER%\n"
            "exit /b %RC%\n",
            encoding="utf-8",
        )
        completed = subprocess.run(
            [env.get("COMSPEC", "cmd.exe"), "/d", "/c", str(wrapper)],
            cwd=PACKAGE_ROOT,
            env=env,
            input="E\n",
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert "RESULT=python" in completed.stdout


def test_launcher_content_survives_a_move_without_machine_paths() -> None:
    original_hash = sha256(LAUNCHER)
    with tempfile.TemporaryDirectory() as temp:
        first = Path(temp) / "First Location"
        second = Path(temp) / "Second Location"
        first.mkdir()
        shutil.copy2(LAUNCHER, first / LAUNCHER.name)
        shutil.move(str(first), str(second))
        moved = second / LAUNCHER.name
        assert sha256(moved) == original_hash
        text = moved.read_text(encoding="utf-8", errors="replace")
        assert "%~dp0" in text
        assert str(first) not in text and str(second) not in text


def main() -> int:
    tests = [
        test_canonical_launcher_is_repo_relative_and_setup_cannot_rewrite_it,
        test_setup_propagates_dependency_failures_and_uses_canonical_requirements,
        test_python_bootstrap_requires_supported_python_and_is_actionable,
        test_python_bootstrap_preserves_supported_path_precedence_on_windows,
        test_launcher_content_survives_a_move_without_machine_paths,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print(f"Launcher portability tests: {len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
