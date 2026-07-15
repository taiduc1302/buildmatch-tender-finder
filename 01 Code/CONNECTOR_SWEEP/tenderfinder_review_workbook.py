r"""Review-workbook discovery (product Task C).

The Track A review workbook is external business data, so a handoff package
must never hard-fail just because one absolute path from the build machine
does not exist. Discovery order:

1. TENDER_FINDER_REVIEW_XLSX environment variable
2. an isolated runtime setting below ``C:\tenderfinder_out\state`` (key:
   ``review_xlsx``, written by the GUI after the user browses once)
3. package-local inputs/all_live_review.xlsx
4. legacy machine path (C:\\tenderfinder_out\\patch5_10_live\\all_live_review.xlsx on
   Windows, ~/tenderfinder_out/patch5_10_live/all_live_review.xlsx elsewhere)

An old package-root JSON file is read only as a migration bridge; new settings
never write into the repository. Pure stdlib, no pipeline imports.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from tenderfinder_runtime import STATE_ROOT_ENV_VAR, default_output_root, runtime_paths

CONFIG_FILENAME = "tenderfinder_runtime_config.json"
PACKAGE_LOCAL_RELATIVE = Path("inputs") / "all_live_review.xlsx"


def legacy_review_xlsx_path() -> Path:
    if sys.platform.startswith("win"):
        return Path(r"C:\tenderfinder_out\patch5_10_live\all_live_review.xlsx")
    return Path.home() / "tenderfinder_out" / "patch5_10_live" / "all_live_review.xlsx"


def _legacy_config_path(root: Path) -> Path:
    return Path(root) / CONFIG_FILENAME


def config_path(root: Path) -> Path:
    """Per-package GUI settings outside the code repository."""
    package_root = Path(root).expanduser().resolve()
    namespace = hashlib.sha256(str(package_root).casefold().encode("utf-8")).hexdigest()[:12]
    selected_state = os.environ.get(STATE_ROOT_ENV_VAR, "").strip() or str(default_output_root() / "state")
    settings = runtime_paths(selected_state, mode="settings", package_root=package_root).settings
    return settings / f"{package_root.name}_{namespace}" / CONFIG_FILENAME


def load_runtime_config(root: Path) -> dict:
    path = config_path(root)
    if not path.exists():
        # Read-only migration bridge for snapshots that already stored this
        # non-secret setting in the package root. New writes never go there.
        legacy = _legacy_config_path(root)
        if legacy.exists():
            path = legacy
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_runtime_config(root: Path, updates: dict) -> Path:
    """Merge non-secret local paths/preferences into isolated runtime state."""
    path = config_path(root)
    config = load_runtime_config(root)
    config.update(updates)
    path.parent.mkdir(parents=True, exist_ok=True)
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
