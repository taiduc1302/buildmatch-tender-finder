from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
sys.path.insert(0, str(ROOT))

from tenderfinder_review_workbook import legacy_review_xlsx_path  # noqa: E402

# The old fast launcher once used a stale absolute snapshot. The current
# invariant is simpler: both compatibility batch launchers default to the
# package-local reviewed workbook and permit one explicit environment override;
# the GUI additionally remembers a selected path in isolated runtime state.

LEGACY = r"C:\tenderfinder_out\patch5_10_live\all_live_review.xlsx"
PACKAGE_LOCAL = r"inputs\all_live_review.xlsx"
STALE_P54 = r"live_outputs_p54\all17_live_review.xlsx"


def _bat_text(name: str) -> str:
    return (REPO_ROOT / name).read_text(encoding="utf-8")


def _bat_initial_value(text: str, name: str) -> str:
    m = re.search(r'set\s+"REVIEW_XLSX=([^"]+)"', text)
    assert m, f"could not find initial REVIEW_XLSX assignment in {name}"
    return m.group(1)


def test_batch_launchers_share_safe_package_local_default() -> None:
    for name in ("run_tenderfinder_demo.bat", "run_tenderfinder_demo_fast.bat"):
        text = _bat_text(name)
        assert _bat_initial_value(text, name) == r"%~dp0inputs\all_live_review.xlsx"
        assert PACKAGE_LOCAL in text, f"{name} must prefer package-local inputs\\all_live_review.xlsx"
        assert "TENDER_FINDER_REVIEW_XLSX" in text, f"{name} must honor the TENDER_FINDER_REVIEW_XLSX env var"
        # Order: env var must be applied AFTER package-local so it wins.
        assert text.index(PACKAGE_LOCAL) < text.index('if defined TENDER_FINDER_REVIEW_XLSX'), (
            f"{name}: env var override must come after the package-local check"
        )


def test_gui_uses_shared_isolated_discovery_helper() -> None:
    gui_text = (ROOT / "tenderfinder_launcher_gui.py").read_text(encoding="utf-8")
    assert "discover_review_xlsx" in gui_text, "GUI must use the shared discovery chain"
    assert "legacy_review_xlsx_path" in gui_text, "GUI legacy fallback must come from the shared helper"
    helper_text = (ROOT / "tenderfinder_review_workbook.py").read_text(encoding="utf-8")
    assert "runtime_paths" in helper_text
    assert "path.write_text" in helper_text
    assert "_legacy_config_path" in helper_text, "old root setting remains read-only migration input"


def test_stale_patch54_snapshot_is_not_the_active_review_xlsx() -> None:
    for name in ("run_tenderfinder_demo.bat", "run_tenderfinder_demo_fast.bat"):
        text = _bat_text(name)
        assert _bat_initial_value(text, name) != STALE_P54, (
            f"{name} still sets REVIEW_XLSX to the stale p54 snapshot"
        )


def test_discovery_chain_order() -> None:
    """Prove the documented order with real temp files: env var beats saved
    config beats package-local beats legacy."""
    import os
    import tempfile
    from tenderfinder_review_workbook import discover_review_xlsx, save_runtime_config
    from tenderfinder_runtime import STATE_ROOT_ENV_VAR

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        root = base / "package"
        root.mkdir()
        old_state = os.environ.get(STATE_ROOT_ENV_VAR)
        old_review = os.environ.get("TENDER_FINDER_REVIEW_XLSX")
        os.environ[STATE_ROOT_ENV_VAR] = str(base / "runtime_state")
        try:
            assert discover_review_xlsx(root)[0] in (None, legacy_review_xlsx_path())

            package_local = root / "inputs" / "all_live_review.xlsx"
            package_local.parent.mkdir()
            package_local.write_text("stub")
            path, source = discover_review_xlsx(root)
            assert path == package_local and "package-local" in source

            config_target = root / "elsewhere.xlsx"
            config_target.write_text("stub")
            saved_path = save_runtime_config(root, {"review_xlsx": str(config_target)})
            assert root not in saved_path.parents, "new runtime setting must stay outside the package root"
            path, source = discover_review_xlsx(root)
            assert path == config_target and "tenderfinder_runtime_config" in source

            env_target = root / "env.xlsx"
            env_target.write_text("stub")
            os.environ["TENDER_FINDER_REVIEW_XLSX"] = str(env_target)
            path, source = discover_review_xlsx(root)
            assert path == env_target and "environment" in source
            # A configured-but-missing higher priority never bricks the run.
            os.environ["TENDER_FINDER_REVIEW_XLSX"] = str(root / "missing.xlsx")
            path, source = discover_review_xlsx(root)
            assert path == config_target, "missing env target must fall through to config"
        finally:
            if old_review is None:
                os.environ.pop("TENDER_FINDER_REVIEW_XLSX", None)
            else:
                os.environ["TENDER_FINDER_REVIEW_XLSX"] = old_review
            if old_state is None:
                os.environ.pop(STATE_ROOT_ENV_VAR, None)
            else:
                os.environ[STATE_ROOT_ENV_VAR] = old_state


def main() -> int:
    tests = [
        test_batch_launchers_share_safe_package_local_default,
        test_gui_uses_shared_isolated_discovery_helper,
        test_stale_patch54_snapshot_is_not_the_active_review_xlsx,
        test_discovery_chain_order,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print("Launcher review-xlsx consistency test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
