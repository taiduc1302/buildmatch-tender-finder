#!/usr/bin/env python3
"""No-write syntax/import smoke check used locally and by offline CI."""
from __future__ import annotations

import importlib
import os
import runpy
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = ROOT / "01 Code" / "CONNECTOR_SWEEP"
OFFLINE_GUARD = CODE_DIR / "tests" / "offline_guard" / "sitecustomize.py"
IMPORTS = (
    "tenderfinder_excel_safety",
    "tenderfinder_url_safety",
    "tenderfinder_package_paths",
    "tenderfinder_runtime",
    "tenderfinder_keywords_config",
    "tenderfinder_source_registry",
    "tenderfinder_source_testing",
    "tenderfinder_bulk_io",
    "tenderfinder_master_io",
    "tenderfinder_demo_three_buckets",
    "tenderfinder_engine",
    "tenderfinder_launcher_gui",
    "tenderfinder_self_test",
)
EXCLUDED_PARTS = {".git", ".venv", ".codex_tmp", "__pycache__", ".pytest_cache"}


def _python_files() -> list[Path]:
    return [
        path
        for path in sorted(ROOT.rglob("*.py"))
        if not EXCLUDED_PARTS.intersection(path.relative_to(ROOT).parts)
    ]


def main() -> int:
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["TENDER_FINDER_OFFLINE_ONLY"] = "1"
    with tempfile.TemporaryDirectory(prefix="tenderfinder_import_check_") as temp:
        attempt_log = Path(temp) / "network_attempts.log"
        os.environ["TENDER_FINDER_NETWORK_GUARD_LOG"] = str(attempt_log)
        runpy.run_path(str(OFFLINE_GUARD), run_name="tenderfinder_ci_offline_guard")

        files = _python_files()
        for path in files:
            source = path.read_text(encoding="utf-8-sig")
            compile(source, str(path), "exec", dont_inherit=True)
        print(f"SYNTAX_CHECK: PASS ({len(files)} Python files, no bytecode written)")

        sys.path.insert(0, str(CODE_DIR))
        for module_name in IMPORTS:
            importlib.import_module(module_name)
        print(f"IMPORT_CHECK: PASS ({len(IMPORTS)} core modules)")

        attempts = attempt_log.read_text(encoding="utf-8").strip() if attempt_log.exists() else ""
        if attempts:
            print("OFFLINE_IMPORT_NETWORK_GUARD: FAIL")
            print(attempts)
            return 1
        print("OFFLINE_IMPORT_NETWORK_GUARD: PASS (0 attempts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
