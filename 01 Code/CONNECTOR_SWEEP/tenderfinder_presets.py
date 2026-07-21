"""Contractor profile presets for TENDER_FINDER / BuildMatch Tender Finder.

Presets are alternate, fully-validated keyword workbooks. The scoring engine is
unchanged and fully data-driven; selecting a preset only points
``load_keywords_config`` at a different workbook. This module is the small,
GUI-independent registry that maps stable preset IDs/versions to those
workbooks, loads them, applies one to an editable copy without clobbering a
customized workbook, and exposes preset identity for run manifests.

No tkinter import — the GUI calls into here.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tenderfinder_package_paths import detect_package_root
from tenderfinder_keywords_config import (
    KeywordConfig,
    clear_keywords_cache,
    load_keywords_config,
)


@dataclass(frozen=True)
class ContractorPreset:
    preset_id: str
    version: str
    display_name: str
    description: str
    workbook: str
    builtin: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "preset_id": self.preset_id,
            "version": self.version,
            "display_name": self.display_name,
            "description": self.description,
            "workbook": self.workbook,
            "builtin": self.builtin,
        }


# Stable IDs + semantic versions. Bump the version when a preset's rules change.
_PRESETS: tuple[ContractorPreset, ...] = (
    ContractorPreset(
        "civil_contractor",
        "1.0.0",
        "Civil Contractor",
        "Civil and earthworks: subdivisions, site servicing, underground "
        "utilities, roadworks and site concrete. Penalizes vertical/interior "
        "building scope. Preserves the original TENDER_FINDER scoring exactly.",
        "civil_contractor.xlsx",
    ),
    ContractorPreset(
        "multifamily_residential",
        "1.0.0",
        "Multi-Family Residential Builder",
        "Multi-family residential construction: apartments, townhomes, condos, "
        "wood-frame and mid-rise. Does not penalize interior, mechanical, "
        "electrical, HVAC or suite scope.",
        "multifamily_residential.xlsx",
    ),
    ContractorPreset(
        "general_contractor",
        "1.0.0",
        "General Contractor",
        "Broad commercial, institutional, residential and light-civil general "
        "contracting. Values both civil site work and vertical building scope.",
        "general_contractor.xlsx",
    ),
)

DEFAULT_PRESET_ID = "civil_contractor"

_BY_ID = {preset.preset_id: preset for preset in _PRESETS}


class PresetError(ValueError):
    """Raised for an unknown preset or an unsafe apply-to-copy operation."""


def presets_dir(root: str | Path | None = None) -> Path:
    package_root = detect_package_root(Path(root).resolve() if root else None)
    return package_root / "config" / "presets"


def list_presets() -> tuple[ContractorPreset, ...]:
    return _PRESETS


def get_preset(preset_id: str) -> ContractorPreset:
    try:
        return _BY_ID[str(preset_id).strip()]
    except KeyError as exc:
        raise PresetError(
            f"unknown preset_id {preset_id!r}; known: {', '.join(sorted(_BY_ID))}"
        ) from exc


def resolve_preset_keywords_path(preset_id: str, *, root: str | Path | None = None) -> Path:
    preset = get_preset(preset_id)
    path = presets_dir(root) / preset.workbook
    if not path.exists():
        raise PresetError(
            f"preset workbook missing: {path} (run config/presets/generate_presets.py)"
        )
    return path.resolve()


def identify_preset(
    keywords_path: str | Path, *, root: str | Path | None = None
) -> ContractorPreset | None:
    """Return the preset whose workbook is ``keywords_path`` (by path), else None."""
    try:
        target = Path(keywords_path).resolve()
    except (OSError, ValueError):
        return None
    directory = presets_dir(root)
    for preset in _PRESETS:
        candidate = (directory / preset.workbook)
        try:
            if candidate.resolve() == target:
                return preset
        except (OSError, ValueError):
            continue
    return None


def load_preset_config(
    preset_id: str,
    *,
    root: str | Path | None = None,
    state_root: str | Path | None = None,
) -> KeywordConfig:
    """Load a preset's keyword configuration (strict; no last-known-good fallback).

    The cache is cleared first so switching presets always reloads.
    """
    path = resolve_preset_keywords_path(preset_id, root=root)
    clear_keywords_cache()
    return load_keywords_config(
        path=path,
        force_reload=True,
        allow_last_known_good=False,
        state_root=state_root,
    )


def apply_preset_to_copy(
    preset_id: str,
    destination: str | Path,
    *,
    root: str | Path | None = None,
    overwrite: bool = False,
) -> Path:
    """Copy a preset workbook to ``destination`` for editing.

    Refuses to overwrite an existing file unless ``overwrite=True`` so a
    founder-customized keyword workbook is never silently clobbered.
    """
    source = resolve_preset_keywords_path(preset_id, root=root)
    dest = Path(destination)
    if dest.exists() and not overwrite:
        raise PresetError(
            f"refusing to overwrite existing workbook without overwrite=True: {dest}"
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return dest.resolve()


def preset_manifest_fields(preset: ContractorPreset) -> dict[str, str]:
    """Fields to embed in a run manifest / dataset provenance for the preset."""
    return {
        "preset_id": preset.preset_id,
        "preset_version": preset.version,
        "preset_display_name": preset.display_name,
    }
