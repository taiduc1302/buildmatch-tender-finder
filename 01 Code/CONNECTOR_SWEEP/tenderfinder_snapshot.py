"""Public-snapshot demo loader/validator/promoter (Build Week Phase 7).

The stable three-minute demo runs against the committed sanitized snapshot under
``demo_data/public_snapshot`` so it never depends on live sites during a
presentation. This module loads the snapshot + manifest, validates that it is
sanitized and internally consistent, exposes it as a ``PUBLIC_SNAPSHOT``
dataset, and can promote it as the active dataset.

No tkinter import.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from tenderfinder_package_paths import detect_package_root
import tenderfinder_data_modes as dm


SNAPSHOT_SUBDIR = ("demo_data", "public_snapshot")
_CSV_NAME = "development_snapshot.csv"
_MANIFEST_NAME = "snapshot_manifest.json"

# Substrings that must never appear in a committed public snapshot.
_FORBIDDEN_MARKERS = (
    "sk-", "api_key", "apikey", "password", "secret",
    "c:\\", "/home/", "/users/", "onedrive", "internal note", "private note",
)


class SnapshotError(RuntimeError):
    """Raised when the snapshot is missing, corrupt, or fails sanitization."""


def snapshot_dir(root: str | Path | None = None) -> Path:
    package_root = detect_package_root(Path(root).resolve() if root else None)
    return package_root.joinpath(*SNAPSHOT_SUBDIR)


def load_snapshot(root: str | Path | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    directory = snapshot_dir(root)
    csv_path = directory / _CSV_NAME
    manifest_path = directory / _MANIFEST_NAME
    if not csv_path.exists() or not manifest_path.exists():
        raise SnapshotError(
            f"snapshot missing under {directory} "
            f"(run demo_data/public_snapshot/generate_snapshot.py)"
        )
    with csv_path.open(encoding="utf-8") as handle:
        records = list(csv.DictReader(handle))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return records, manifest


def _content_hash(root: str | Path | None = None) -> str:
    return hashlib.sha256((snapshot_dir(root) / _CSV_NAME).read_bytes()).hexdigest()


def validate_snapshot(root: str | Path | None = None) -> dict[str, Any]:
    """Return {'passed': bool, 'errors': [...]} for the committed snapshot."""
    errors: list[str] = []
    records, manifest = load_snapshot(root)

    if manifest.get("data_mode") != dm.MODE_PUBLIC_SNAPSHOT:
        errors.append("manifest data_mode is not PUBLIC_SNAPSHOT")
    if manifest.get("record_count") != len(records):
        errors.append("manifest record_count does not match the dataset")
    if manifest.get("content_hash") != _content_hash(root):
        errors.append("content_hash does not match the dataset (snapshot was edited)")
    if not manifest.get("capture_timestamp"):
        errors.append("manifest has no capture_timestamp")
    if not manifest.get("source_provenance"):
        errors.append("manifest has no source_provenance")

    # Sanitization: no secrets, local paths, or private notes in the record
    # payload or the source-provenance URLs. The manifest's own descriptive text
    # (which legitimately says "no secrets/internal notes") is not scanned.
    blob = (
        json.dumps(records, ensure_ascii=False)
        + json.dumps(manifest.get("source_provenance", []))
    ).lower()
    for marker in _FORBIDDEN_MARKERS:
        if marker in blob:
            errors.append(f"forbidden marker present in snapshot: {marker!r}")

    return {"passed": not errors, "errors": errors}


def snapshot_provenance(root: str | Path | None = None) -> dm.DatasetProvenance:
    records, manifest = load_snapshot(root)
    validation = validate_snapshot(root)
    return dm.DatasetProvenance(
        dataset_id=manifest.get("snapshot_id", "public_snapshot"),
        path=str(snapshot_dir(root) / _CSV_NAME),
        data_mode=dm.MODE_PUBLIC_SNAPSHOT,
        capture_timestamp=manifest.get("capture_timestamp", ""),
        source_ids=tuple(s.get("source_id", "") for s in manifest.get("source_provenance", [])),
        source_results=tuple(manifest.get("source_provenance", [])),
        record_counts={"total": len(records), "snapshot": len(records)},
        validation=validation,
        content_hash=manifest.get("content_hash", ""),
        preset_id=manifest.get("acceptance", {}).get("preset_id", ""),
    )


def promote_snapshot(
    *,
    state_root: str | Path | None = None,
    root: str | Path | None = None,
) -> dm.PromotionResult:
    """Make the validated public snapshot the active dataset."""
    provenance = snapshot_provenance(root)
    if not provenance.is_valid:
        return dm.PromotionResult(
            promoted=False, reason="validation_failed", active=None, previous=None,
            errors=tuple(provenance.validation.get("errors", ())),
        )
    return dm.promote_dataset(provenance, state_root=state_root, package_root=root)


def acceptance_expectations(root: str | Path | None = None) -> dict[str, Any]:
    _records, manifest = load_snapshot(root)
    return manifest.get("acceptance", {})
