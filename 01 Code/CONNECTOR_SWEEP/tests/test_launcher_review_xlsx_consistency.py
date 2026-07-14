from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
sys.path.insert(0, str(ROOT))

from tenderfinder_review_workbook import legacy_review_xlsx_path  # noqa: E402

# Patch 5.18 origin: run_tenderfinder_demo_fast.bat pointed at a stale review
# workbook and silently produced different Track A totals than full mode
# and the GUI. Patch 5.20 (product Task C) replaced the single hardcoded
# path with a discovery chain (TENDER_FINDER_REVIEW_XLSX env var -> saved config ->
# package-local inputs\ -> legacy machine path). The invariant these tests
# now lock: every launch path implements the SAME chain with the SAME
# fallbacks, so fast/full/GUI can never disagree on the Track A workbook.

LEGACY = r"C:\tenderfinder_out\patch5_10_live\all_live_review.xlsx"
PACKAGE_LOCAL = r"inputs\all_live_review.xlsx"
STALE_P54 = r"live_outputs_p54\all17_live_review.xlsx"


def _bat_text(name: str) -> str:
    return (REPO_ROOT / name).read_text(encoding="utf-8")


def _bat_legacy_value(text: str, name: str) -> str:
    m = re.search(r'set\s+"REVIEW_XLSX=([^"]+)"', text)
    assert m, f"could not find initial REVIEW_XLSX assignment in {name}"
    return m.group(1)


def test_batch_launchers_share_the_same_discovery_chain() -> None:
    for name in ("run_tenderfinder_demo.bat", "run_tenderfinder_demo_fast.bat"):
        text = _bat_text(name)
        assert _bat_legacy_value(text, name) == LEGACY, f"{name} legacy fallback drifted"
        assert PACKAGE_LOCAL in text, f"{name} must prefer package-local inputs\\all_live_review.xlsx"
        assert "TENDER_FINDER_REVIEW_XLSX" in text, f"{name} must honor the TENDER_FINDER_REVIEW_XLSX env var"
        # Order: env var must be applied AFTER package-local so it wins.
        assert text.index(PACKAGE_LOCAL) < text.index('if defined TENDER_FINDER_REVIEW_XLSX'), (
            f"{name}: env var override must come after the package-local check"
        )


def test_gui_legacy_fallback_matches_batch_launchers() -> None:
    if sys.platform.startswith("win"):
        assert str(legacy_review_xlsx_path()) == LEGACY, (
            "tenderfinder_review_workbook.legacy_review_xlsx_path() must match the "
            ".bat launchers' legacy fallback"
        )
    gui_text = (ROOT / "tenderfinder_launcher_gui.py").read_text(encoding="utf-8")
    assert "discover_review_xlsx" in gui_text, "GUI must use the shared discovery chain"
    assert "legacy_review_xlsx_path" in gui_text, "GUI legacy fallback must come from the shared helper"


def test_stale_patch54_snapshot_is_not_the_active_review_xlsx() -> None:
    for name in ("run_tenderfinder_demo.bat", "run_tenderfinder_demo_fast.bat"):
        text = _bat_text(name)
        assert _bat_legacy_value(text, name) != STALE_P54, (
            f"{name} still sets REVIEW_XLSX to the stale p54 snapshot"
        )


def test_discovery_chain_order() -> None:
    """Prove the documented order with real temp files: env var beats saved
    config beats package-local beats legacy."""
    import os
    import tempfile
    from tenderfinder_review_workbook import discover_review_xlsx, save_runtime_config

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert discover_review_xlsx(root)[0] in (None, legacy_review_xlsx_path())

        package_local = root / "inputs" / "all_live_review.xlsx"
        package_local.parent.mkdir()
        package_local.write_text("stub")
        path, source = discover_review_xlsx(root)
        assert path == package_local and "package-local" in source

        config_target = root / "elsewhere.xlsx"
        config_target.write_text("stub")
        save_runtime_config(root, {"review_xlsx": str(config_target)})
        path, source = discover_review_xlsx(root)
        assert path == config_target and "tenderfinder_runtime_config" in source

        env_target = root / "env.xlsx"
        env_target.write_text("stub")
        old = os.environ.get("TENDER_FINDER_REVIEW_XLSX")
        try:
            os.environ["TENDER_FINDER_REVIEW_XLSX"] = str(env_target)
            path, source = discover_review_xlsx(root)
            assert path == env_target and "environment" in source
            # A configured-but-missing higher priority never bricks the run.
            os.environ["TENDER_FINDER_REVIEW_XLSX"] = str(root / "missing.xlsx")
            path, source = discover_review_xlsx(root)
            assert path == config_target, "missing env target must fall through to config"
        finally:
            if old is None:
                os.environ.pop("TENDER_FINDER_REVIEW_XLSX", None)
            else:
                os.environ["TENDER_FINDER_REVIEW_XLSX"] = old


def main() -> int:
    tests = [
        test_batch_launchers_share_the_same_discovery_chain,
        test_gui_legacy_fallback_matches_batch_launchers,
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
