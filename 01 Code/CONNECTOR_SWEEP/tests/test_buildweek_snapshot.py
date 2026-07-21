"""Tests for the public-snapshot demo + source-registry truthfulness
(Build Week Phases 7 and 8).

Runs under pytest and as a script.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPO_ROOT = ROOT.parents[1]

import tenderfinder_snapshot as snap  # noqa: E402
import tenderfinder_data_modes as dm  # noqa: E402
import tenderfinder_guards as G  # noqa: E402
from tenderfinder_keywords_config import clear_keywords_cache  # noqa: E402
from tenderfinder_presets import resolve_preset_keywords_path  # noqa: E402


def test_snapshot_loads_and_validates() -> None:
    records, manifest = snap.load_snapshot(REPO_ROOT)
    assert len(records) == manifest["record_count"]
    validation = snap.validate_snapshot(REPO_ROOT)
    assert validation["passed"], validation["errors"]


def test_snapshot_is_sanitized() -> None:
    validation = snap.validate_snapshot(REPO_ROOT)
    assert validation["passed"], validation["errors"]
    records, _manifest = snap.load_snapshot(REPO_ROOT)
    blob = " ".join(str(v) for r in records for v in r.values()).lower()
    for forbidden in ("sk-", "c:\\", "/home/", "password", "onedrive"):
        assert forbidden not in blob


def test_snapshot_provenance_is_public_snapshot() -> None:
    prov = snap.snapshot_provenance(REPO_ROOT)
    assert prov.data_mode == dm.MODE_PUBLIC_SNAPSHOT
    assert prov.capture_timestamp
    assert prov.source_ids
    assert "PUBLIC SNAPSHOT — captured" in prov.banner_text()


def test_snapshot_scoring_meets_acceptance_ranges() -> None:
    records, manifest = snap.load_snapshot(REPO_ROOT)
    acceptance = manifest["acceptance"]
    os.environ["TENDER_FINDER_KEYWORDS_CONFIG"] = str(
        resolve_preset_keywords_path(acceptance["preset_id"], root=REPO_ROOT)
    )
    try:
        ge60 = 0
        for record in records:
            clear_keywords_cache()
            fit = G.score_civil_fit(record["scope_summary"] + " " + record["app_type_stage"])
            expected = acceptance["per_record"][record["record_id"]]
            assert expected["min_fit"] <= fit <= expected["max_fit"], (
                f"{record['record_id']} fit {fit} outside {expected}"
            )
            ge60 += 1 if fit >= 60 else 0
        assert ge60 >= acceptance["min_records_fit_ge_60"]
    finally:
        os.environ.pop("TENDER_FINDER_KEYWORDS_CONFIG", None)
        clear_keywords_cache()


def test_snapshot_promotes_as_active_dataset() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "state"
        result = snap.promote_snapshot(state_root=state, root=REPO_ROOT)
        assert result.promoted, result.errors
        active = dm.load_active_dataset(state_root=state, package_root=REPO_ROOT)
        assert active is not None and active.data_mode == dm.MODE_PUBLIC_SNAPSHOT


def test_source_registry_keeps_vancouver_needs_configuration() -> None:
    # Phase 8: Vancouver rezoning/dev-permit sources must not be runnable.
    import tenderfinder_refresh_service as rs

    health = {row["source_id"]: row for row in
              rs.source_health_rows(package_root=REPO_ROOT)}
    for sid in ("van_rezoning", "van_devpermits"):
        assert sid in health
        assert health[sid]["status"] == "needs_configuration"
        assert health[sid]["runtime_eligible"] is False


def main() -> int:
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print(f"Build Week snapshot/source tests: {len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
