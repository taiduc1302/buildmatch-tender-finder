from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "offline-ci.yml"
CHECK_SCRIPT = REPO_ROOT / "scripts" / "offline_ci_check.py"


def test_workflow_is_valid_windows_offline_ci() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    parsed = yaml.safe_load(text)
    assert isinstance(parsed, dict)
    assert "windows-latest" in text
    assert "tenderfinder_self_test.py" in text
    assert "scripts/offline_ci_check.py" in text
    assert "playwright install" not in text.casefold()
    assert "live source" not in text.casefold()
    assert "secrets." not in text.casefold()
    assert "permissions:" in text and "contents: read" in text


def test_local_ci_check_passes_without_network_or_bytecode() -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, str(CHECK_SCRIPT)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "SYNTAX_CHECK: PASS" in completed.stdout
    assert "IMPORT_CHECK: PASS" in completed.stdout
    assert "OFFLINE_IMPORT_NETWORK_GUARD: PASS" in completed.stdout


def main() -> int:
    tests = [
        test_workflow_is_valid_windows_offline_ci,
        test_local_ci_check_passes_without_network_or_bytecode,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print(f"Offline CI workflow tests: {len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
