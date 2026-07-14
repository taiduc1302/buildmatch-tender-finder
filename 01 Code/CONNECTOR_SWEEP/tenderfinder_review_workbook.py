"""Review-workbook discovery (product Task C).

The Track A review workbook is external business data, so a handoff package
must never hard-fail just because one absolute path from the build machine
does not exist. Discovery order:

1. TENDER_FINDER_REVIEW_XLSX environment variable
2. tenderfinder_runtime_config.json in the package/repo root (key: "review_xlsx",
   written by the GUI when the user browses to the workbook once)
3. package-local inputs/all_live_review.xlsx
4. legacy machine path (C:\\tenderfinder_out\\patch5_10_live\\all_live_review.xlsx on
   Windows, ~/tenderfinder_out/patch5_10_live/all_live_review.xlsx elsewhere)

Pure stdlib, no pipeline imports - safe for the GUI (which deliberately
never imports the demo builder) and for tests.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CONFIG_FILENAME = "tenderfinder_runtime_config.json"
PACKAGE_LOCAL_RELATIVE = Path("inputs") / "all_live_review.xlsx"


def legacy_review_xlsx_path() -> Path:
    if sys.platform.startswith("win"):
        return Path(r"C:\tenderfinder_out\patch5_10_live\all_live_review.xlsx")
    return Path.home() / "tenderfinder_out" / "patch5_10_live" / "all_live_review.xlsx"


def config_path(root: Path) -> Path:
    return root / CONFIG_FILENAME


def load_runtime_config(root: Path) -> dict:
    path = config_path(root)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_runtime_config(root: Path, updates: dict) -> Path:
    """Merge updates into the package-local config. Never stores secrets -
    only local file paths and preferences."""
    path = config_path(root)
    config = load_runtime_config(root)
    config.update(updates)
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path


def discover_review_xlsx(root: Path) -> tuple[Path | None, str]:
    """Return (path, source_label) for the first existing candidate in the
    documented order, or (None, 'not_found') if nothing exists. Candidates
    that are configured but missing are skipped (not fatal) so a stale
    config entry can never brick the launcher."""
    env_value = os.environ.get("TENDER_FINDER_REVIEW_XLSX", "").strip()
    if env_value:
        p = Path(env_value)
        if p.exists():
            return p, "TENDER_FINDER_REVIEW_XLSX environment variable"

    config_value = str(load_runtime_config(root).get("review_xlsx", "") or "").strip()
    if config_value:
        p = Path(config_value)
        if p.exists():
            return p, f"saved setting in {CONFIG_FILENAME}"

    package_local = root / PACKAGE_LOCAL_RELATIVE
    if package_local.exists():
        return package_local, "package-local inputs folder"

    legacy = legacy_review_xlsx_path()
    if legacy.exists():
        return legacy, "legacy machine path"

    return None, "not_found"


def missing_workbook_explanation(root: Path) -> str:
    """Plain-English text for the GUI dialog when nothing was found."""
    return (
        "TENDER_FINDER needs the reviewed-leads workbook (all_live_review.xlsx) to build "
        "Track A - the BID LATER / Watchlist / Analyzed intelligence.\n\n"
        "None of the usual locations had it:\n"
        f"  1. TENDER_FINDER_REVIEW_XLSX environment variable (not set or file missing)\n"
        f"  2. {config_path(root)} (no saved path)\n"
        f"  3. {root / PACKAGE_LOCAL_RELATIVE}\n"
        f"  4. {legacy_review_xlsx_path()}\n\n"
        "Click OK to browse for the workbook. Your choice will be remembered "
        "for future runs."
    )
