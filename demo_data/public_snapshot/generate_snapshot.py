"""Deterministically regenerate the sanitized PUBLIC SNAPSHOT demo dataset.

The three-minute competition demo runs against this stable, offline snapshot so
it never depends on live sites during a presentation. The records are
fictitious-but-realistic British Columbia development-application leads. They
carry NO secrets, NO internal notes, NO local filesystem paths and NO
unnecessary personal data — only the kind of public fields a municipal
development feed exposes. Applicant names are invented.

Outputs (committed):
* ``development_snapshot.csv``  — the sanitized records.
* ``snapshot_manifest.json``    — capture timestamp, source provenance, content
  hash, per-record expected fit ranges/tier, and aggregate acceptance values.

Run: ``python demo_data/public_snapshot/generate_snapshot.py``
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

# A fixed capture timestamp keeps the snapshot reproducible (do not use now()).
CAPTURE_TIMESTAMP = "2026-07-19T09:00:00-07:00"
SNAPSHOT_ID = "public_snapshot_2026_07_19"

FIELDS = [
    "record_id", "municipality", "app_no", "address", "app_type_stage",
    "status_class", "scope_summary", "applicant_name", "source", "source_url",
]

# Source provenance: public municipal development feeds (IDs match sources.csv).
SOURCES = [
    {"source_id": "surrey_devapps_v2", "name": "City of Surrey Development Applications",
     "public_url": "https://data.surrey.ca/"},
    {"source_id": "maple_ridge_devapps", "name": "Maple Ridge Development Applications",
     "public_url": "https://www.mapleridge.ca/"},
    {"source_id": "twp_langley_devactivity", "name": "Township of Langley Development Activity",
     "public_url": "https://www.tol.ca/"},
]

# Each record carries an expected civil-preset fit range + coarse tier so the
# snapshot doubles as an acceptance fixture. Ranges are intentionally wide.
RECORDS = [
    {
        "record_id": "SNAP-001", "municipality": "Surrey", "app_no": "7926-0100-00",
        "address": "18200 Fraser Highway", "app_type_stage": "Subdivision Application",
        "status_class": "OPEN",
        "scope_summary": "New multi-lot subdivision requiring full site servicing, watermain, "
                         "sanitary sewer, storm drainage, grading and roadworks.",
        "applicant_name": "Fraser Ridge Land Corp", "source": "surrey_devapps_v2",
        "source_url": "https://data.surrey.ca/dataset/development-applications/SNAP-001",
        "_expected": {"min_fit": 80, "max_fit": 100, "tier": "HIGH"},
    },
    {
        "record_id": "SNAP-002", "municipality": "Maple Ridge", "app_no": "2026-045-DP",
        "address": "11800 224 Street", "app_type_stage": "Development Permit",
        "status_class": "OPEN",
        "scope_summary": "Watermain and sanitary sewer replacement with road restoration and "
                         "curb and gutter for an infill servicing project.",
        "applicant_name": "Ridgeline Servicing Ltd", "source": "maple_ridge_devapps",
        "source_url": "https://www.mapleridge.ca/devapps/SNAP-002",
        "_expected": {"min_fit": 80, "max_fit": 100, "tier": "HIGH"},
    },
    {
        "record_id": "SNAP-003", "municipality": "Langley", "app_no": "DA-2026-118",
        "address": "8400 208 Street", "app_type_stage": "Development Activity",
        "status_class": "OPEN",
        "scope_summary": "Road and utility site servicing including storm sewer, forcemain, "
                         "manhole installation and earthworks for an industrial parcel.",
        "applicant_name": "Willoughby Industrial GP", "source": "twp_langley_devactivity",
        "source_url": "https://www.tol.ca/devactivity/SNAP-003",
        "_expected": {"min_fit": 80, "max_fit": 100, "tier": "HIGH"},
    },
    {
        "record_id": "SNAP-004", "municipality": "Surrey", "app_no": "7926-0210-00",
        "address": "15300 105 Avenue", "app_type_stage": "Rezoning",
        "status_class": "OPEN",
        "scope_summary": "Rezoning and land development for a multi-family residential project "
                         "with associated site servicing and utility connections.",
        "applicant_name": "Guildford Housing Partners", "source": "surrey_devapps_v2",
        "source_url": "https://data.surrey.ca/dataset/development-applications/SNAP-004",
        "_expected": {"min_fit": 55, "max_fit": 100, "tier": "MEDIUM"},
    },
    {
        "record_id": "SNAP-005", "municipality": "Maple Ridge", "app_no": "2026-061-DP",
        "address": "20500 Lougheed Highway", "app_type_stage": "Development Permit",
        "status_class": "OPEN",
        "scope_summary": "Storm drainage culvert replacement and detention pond construction "
                         "with trench and pipe works.",
        "applicant_name": "Alouette Civil Works", "source": "maple_ridge_devapps",
        "source_url": "https://www.mapleridge.ca/devapps/SNAP-005",
        "_expected": {"min_fit": 70, "max_fit": 100, "tier": "HIGH"},
    },
    {
        "record_id": "SNAP-006", "municipality": "Langley", "app_no": "DA-2026-140",
        "address": "6100 200 Street", "app_type_stage": "Building Permit",
        "status_class": "OPEN",
        "scope_summary": "Interior tenant improvement of an existing office suite including "
                         "mechanical, electrical and HVAC alterations.",
        "applicant_name": "Cornerstone Interiors Inc", "source": "twp_langley_devactivity",
        "source_url": "https://www.tol.ca/devactivity/SNAP-006",
        "_expected": {"min_fit": 0, "max_fit": 20, "tier": "LOW"},
    },
    {
        "record_id": "SNAP-007", "municipality": "Surrey", "app_no": "7926-0330-00",
        "address": "13400 King George Boulevard", "app_type_stage": "Development Permit",
        "status_class": "OPEN",
        "scope_summary": "Sanitary sewer forcemain extension and lift station upgrade with "
                         "underground utility works.",
        "applicant_name": "Newton Underground Utilities", "source": "surrey_devapps_v2",
        "source_url": "https://data.surrey.ca/dataset/development-applications/SNAP-007",
        "_expected": {"min_fit": 80, "max_fit": 100, "tier": "HIGH"},
    },
    {
        "record_id": "SNAP-008", "municipality": "Maple Ridge", "app_no": "2026-072-SP",
        "address": "22300 Dewdney Trunk Road", "app_type_stage": "Sign Permit",
        "status_class": "OPEN",
        "scope_summary": "New freestanding commercial sign permit; no site or servicing work.",
        "applicant_name": "Haney Signage Co", "source": "maple_ridge_devapps",
        "source_url": "https://www.mapleridge.ca/devapps/SNAP-008",
        "_expected": {"min_fit": 0, "max_fit": 40, "tier": "LOW"},
    },
]


def _write_csv(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for record in RECORDS:
            writer.writerow({field: record[field] for field in FIELDS})


def _content_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    csv_path = HERE / "development_snapshot.csv"
    _write_csv(csv_path)
    manifest = {
        "schema_version": 1,
        "snapshot_id": SNAPSHOT_ID,
        "data_mode": "PUBLIC_SNAPSHOT",
        "capture_timestamp": CAPTURE_TIMESTAMP,
        "dataset_file": csv_path.name,
        "content_hash": _content_hash(csv_path),
        "record_count": len(RECORDS),
        "sanitization": (
            "Fictitious-but-realistic public development-application records. No "
            "secrets, internal notes, local paths, or unnecessary personal data. "
            "Applicant names are invented."
        ),
        "source_provenance": SOURCES,
        "acceptance": {
            "preset_id": "civil_contractor",
            "min_records_fit_ge_60": 4,
            "per_record": {
                record["record_id"]: record["_expected"] for record in RECORDS
            },
        },
    }
    (HERE / "snapshot_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(RECORDS)} snapshot records + manifest to {HERE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
