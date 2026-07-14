from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
sys.path.insert(0, str(ROOT))

# Patch 5.19: the macOS handoff package is assembled from the canonical
# scripts in packaging/macos/. These tests run against the canonical copies
# (which ARE committed) and, when the assembled TENDER_FINDER_Handoff_Package_macOS
# folder exists at repo root, against that too. They prove the scripts are
# actually mac-runnable: bash shebang, self-locating, LF-only line endings,
# and no Windows-only paths like .venv\Scripts or C:\ drives.

CANONICAL_DIR = REPO_ROOT / "packaging" / "macos"
PACKAGE_DIR = REPO_ROOT / "TENDER_FINDER_Handoff_Package_macOS"

COMMAND_SCRIPTS = [
    "setup_tenderfinder_environment.command",
    "Launch_TENDER_FINDER_GUI.command",
    "run_tenderfinder_demo.command",
    "run_tenderfinder_demo_fast.command",
]
MAC_DOCS = ["START_HERE_MAC.md", "FILES_EXPLAINED_MAC.md"]

WINDOWS_ONLY_MARKERS = [".venv\\Scripts", "C:\\tenderfinder_out", "C:\\t\\", "taskkill", "%~dp0", "cmd /c"]


def _script_dirs() -> list[Path]:
    dirs = [CANONICAL_DIR]
    if PACKAGE_DIR.exists():
        dirs.append(PACKAGE_DIR)
    return dirs


def test_canonical_macos_scripts_exist() -> None:
    for name in COMMAND_SCRIPTS + MAC_DOCS:
        path = CANONICAL_DIR / name
        assert path.exists(), f"missing canonical macOS file: {path}"


def test_command_scripts_are_bash_and_self_locating() -> None:
    for d in _script_dirs():
        for name in COMMAND_SCRIPTS:
            text = (d / name).read_text(encoding="utf-8")
            assert text.startswith("#!/bin/bash"), f"{d / name} must start with #!/bin/bash"
            assert 'cd "$(dirname "$0")"' in text, f"{d / name} must self-locate with cd \"$(dirname \"$0\")\""


def test_command_scripts_have_lf_only_line_endings() -> None:
    """CRLF in a shebang line breaks with 'bad interpreter' on macOS."""
    for d in _script_dirs():
        for name in COMMAND_SCRIPTS:
            raw = (d / name).read_bytes()
            assert b"\r" not in raw, f"{d / name} contains CR bytes - must be LF-only"


def test_command_scripts_contain_no_windows_only_paths() -> None:
    for d in _script_dirs():
        for name in COMMAND_SCRIPTS:
            text = (d / name).read_text(encoding="utf-8")
            for marker in WINDOWS_ONLY_MARKERS:
                assert marker not in text, f"{d / name} contains Windows-only marker {marker!r}"


def test_setup_uses_python3_venv_and_posix_python() -> None:
    text = (CANONICAL_DIR / "setup_tenderfinder_environment.command").read_text(encoding="utf-8")
    assert "python3 -m venv .venv" in text
    assert ".venv/bin/python" in text
    assert "playwright install chromium" in text
    assert "chmod +x" in text


def test_gui_launcher_prefers_pythonw_when_available() -> None:
    text = (CANONICAL_DIR / "Launch_TENDER_FINDER_GUI.command").read_text(encoding="utf-8")
    assert ".venv/bin/pythonw" in text, "should use pythonw when the venv provides it"
    assert ".venv/bin/python" in text, "must fall back to plain python"
    assert "tenderfinder_launcher_gui.py" in text


def _review_legacy_default(script_name: str) -> str:
    text = (CANONICAL_DIR / script_name).read_text(encoding="utf-8")
    m = re.search(r'REVIEW_XLSX="(\$HOME[^"]+)"', text)
    assert m, f"could not find REVIEW_XLSX legacy default in {script_name}"
    return m.group(1)


def test_full_and_fast_command_launchers_agree_on_review_workbook() -> None:
    """Same invariant the Windows launchers are held to (Patch 5.18/5.20):
    fast and full mode must never silently disagree on the Track A workbook,
    and both must implement the same discovery chain (env var > package-local
    inputs/ > legacy home path)."""
    full = _review_legacy_default("run_tenderfinder_demo.command")
    fast = _review_legacy_default("run_tenderfinder_demo_fast.command")
    assert full == fast, f"full uses {full!r} but fast uses {fast!r}"
    full_text = (CANONICAL_DIR / "run_tenderfinder_demo.command").read_text(encoding="utf-8")
    fast_text = (CANONICAL_DIR / "run_tenderfinder_demo_fast.command").read_text(encoding="utf-8")
    assert "--no-fetch" in fast_text
    assert "--no-fetch" not in full_text
    for text, name in [(full_text, "full"), (fast_text, "fast")]:
        assert "TENDER_FINDER_REVIEW_XLSX" in text, f"{name} must honor the env override"
        assert "inputs/all_live_review.xlsx" in text, f"{name} must prefer the package-local workbook"
        assert text.index("inputs/all_live_review.xlsx") < text.index('"${TENDER_FINDER_REVIEW_XLSX:-}"'), (
            f"{name}: env override must be applied after the package-local check so it wins"
        )


def test_assembled_package_hygiene_if_present() -> None:
    """When the assembled macOS package folder exists, it must contain the
    runtime + data files and no venv/pycache/git internals or secrets."""
    if not PACKAGE_DIR.exists():
        print("  (assembled TENDER_FINDER_Handoff_Package_macOS not present - canonical-only run)")
        return
    required = COMMAND_SCRIPTS + MAC_DOCS + [
        "01 Code/CONNECTOR_SWEEP/tenderfinder_demo_three_buckets.py",
        "01 Code/CONNECTOR_SWEEP/tenderfinder_launcher_gui.py",
        "01 Code/CONNECTOR_SWEEP/tenderfinder_source_backlog.py",
        "01 Code/CONNECTOR_SWEEP/requirements.txt",
        "01 Code/CONNECTOR_SWEEP/data/TENDER_FINDER_Source_Universe_Backlog_v2_EXPANDED.xlsx",
        "01 Code/CONNECTOR_SWEEP/data/TENDER_FINDER_Potential_Unaccounted_Sources_v2_EXPANDED.csv",
    ]
    for rel in required:
        assert (PACKAGE_DIR / rel).exists(), f"package missing {rel}"
    forbidden_dirs = {".venv", "__pycache__", ".git", "tests"}
    forbidden_names = {"gui_run_error.log"}
    for p in PACKAGE_DIR.rglob("*"):
        assert p.name not in forbidden_dirs, f"package must not contain {p}"
        assert p.name not in forbidden_names, f"package must not contain {p}"
        low = p.name.lower()
        assert "cookie" not in low and "token" not in low and "secret" not in low, f"suspicious file in package: {p}"


def main() -> int:
    tests = [
        test_canonical_macos_scripts_exist,
        test_command_scripts_are_bash_and_self_locating,
        test_command_scripts_have_lf_only_line_endings,
        test_command_scripts_contain_no_windows_only_paths,
        test_setup_uses_python3_venv_and_posix_python,
        test_gui_launcher_prefers_pythonw_when_available,
        test_full_and_fast_command_launchers_agree_on_review_workbook,
        test_assembled_package_hygiene_if_present,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print("macOS package scripts test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
