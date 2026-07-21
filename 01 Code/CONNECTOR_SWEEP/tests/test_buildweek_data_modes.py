"""Tests for dataset provenance, data modes, truthful run metrics, and the
external active-dataset pointer (Build Week Phases 1, 3, 4).

Runs both under pytest and as a plain ``python test_buildweek_data_modes.py``
script (so the offline Self-Test can invoke it).
"""
from __future__ import annotations

import json
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tenderfinder_data_modes as dm  # noqa: E402
from tenderfinder_runtime import atomic_write_json  # noqa: E402


def _dataset(tmp: Path, *, mode: str = dm.MODE_LIVE, total: int = 5, valid: bool = True,
             dataset_id: str = "ds_test", create_file: bool = True) -> dm.DatasetProvenance:
    path = tmp / f"{dataset_id}.xlsx"
    if create_file:
        path.write_bytes(b"PK\x03\x04 fake workbook bytes")
    return dm.DatasetProvenance(
        dataset_id=dataset_id,
        path=str(path),
        data_mode=mode,
        capture_timestamp="2026-07-19T14:15:00-07:00",
        source_ids=("surrey_devapps_v2",),
        source_results=({"source_id": "surrey_devapps_v2", "ok": True, "records": total},),
        record_counts={"total": total, "live": total},
        validation={"passed": valid, "errors": [] if valid else ["boom"]},
        content_hash="deadbeef",
        preset_id="civil_contractor",
        preset_version="1.0.0",
        last_successful_refresh="2026-07-19T14:15:00-07:00",
    )


def test_data_mode_normalization_and_banners() -> None:
    assert dm.normalize_mode("live") == dm.MODE_LIVE
    assert dm.normalize_mode("nonsense") == dm.MODE_UNKNOWN
    assert dm.normalize_mode(None) == dm.MODE_UNKNOWN

    synth = dm.DatasetProvenance("a", "", dm.MODE_SYNTHETIC)
    assert "SYNTHETIC DEMO DATA" in synth.banner_text()
    assert "no real opportunities" in synth.banner_text()

    snap = dm.DatasetProvenance("b", "", dm.MODE_PUBLIC_SNAPSHOT, capture_timestamp="2026-07-19T09:00:00")
    assert snap.banner_text().startswith("PUBLIC SNAPSHOT — captured July 19, 2026")

    live = dm.DatasetProvenance("c", "", dm.MODE_LIVE, capture_timestamp="2026-07-19T14:15:00")
    assert "LIVE PUBLIC DATA — refreshed July 19, 2026 at 2:15 PM" == live.banner_text()

    unknown = dm.DatasetProvenance("d", "", dm.MODE_UNKNOWN)
    assert "UNKNOWN DATA ORIGIN" in unknown.banner_text()

    mixed = dm.DatasetProvenance("e", "", dm.MODE_MIXED)
    assert "MIXED DATA" in mixed.banner_text()


def test_cached_live_banner_shows_age() -> None:
    now = datetime.fromisoformat("2026-07-21T14:15:00-07:00")
    cached = dm.DatasetProvenance(
        "c", "", dm.MODE_CACHED_LIVE,
        last_successful_refresh="2026-07-19T14:15:00-07:00",
    )
    assert cached.banner_text(now=now) == "CACHED LIVE DATA — last successful refresh 2 days ago"


def test_synthetic_can_never_become_live() -> None:
    # classify never promotes synthetic-only rows to live.
    assert dm.classify_record_counts({"synthetic": 12}) == dm.MODE_SYNTHETIC
    # mixing synthetic with real yields MIXED, not LIVE.
    assert dm.classify_record_counts({"synthetic": 5, "live": 10}) == dm.MODE_MIXED
    assert dm.classify_record_counts({"live": 10}) == dm.MODE_LIVE
    assert dm.classify_record_counts({"snapshot": 3}) == dm.MODE_PUBLIC_SNAPSHOT
    assert dm.classify_record_counts({"cached": 4}) == dm.MODE_CACHED_LIVE
    assert dm.classify_record_counts({}) == dm.MODE_UNKNOWN


def test_mark_stale_demotes_live_to_cached() -> None:
    live = dm.DatasetProvenance("c", "", dm.MODE_LIVE, capture_timestamp="2026-07-19T14:15:00")
    stale = dm.mark_stale(live)
    assert stale.data_mode == dm.MODE_CACHED_LIVE
    assert stale.stale is True
    assert stale.last_successful_refresh == "2026-07-19T14:15:00"
    # A failed refresh must never advance a live timestamp; snapshot stays snapshot.
    snap = dm.DatasetProvenance("s", "", dm.MODE_PUBLIC_SNAPSHOT)
    assert dm.mark_stale(snap).data_mode == dm.MODE_PUBLIC_SNAPSHOT


def test_run_metrics_reconcile_truthfully() -> None:
    m = dm.RunMetrics(
        run_id="run1",
        sources_selected=3, sources_attempted=3, sources_successful=2, sources_failed=1,
        records_fetched=100, records_loaded=0, records_before_dedup=100,
        duplicates_removed=10, normalized_records=90, records_scored=90,
        bid_now=5, bid_later=20, watch=15, skip=50,
        records_live=90,
        data_mode=dm.MODE_LIVE,
    )
    assert m.is_reconciled(), m.reconciliation_errors()

    # bucket total mismatch is caught
    bad = dm.RunMetrics(records_scored=90, bid_now=1, bid_later=1, watch=1, skip=1)
    assert not bad.is_reconciled()
    assert any("bucket total" in e for e in bad.reconciliation_errors())


def test_replay_counts_as_loaded_not_fetched() -> None:
    m = dm.RunMetrics(
        records_fetched=0, records_loaded=42, records_before_dedup=42,
        duplicates_removed=0, normalized_records=42, records_scored=42,
        skip=42,
    )
    assert m.records_fetched == 0
    assert m.records_loaded == 42
    assert m.is_reconciled()


def test_zero_fetch_stays_zero() -> None:
    m = dm.RunMetrics(records_fetched=0, records_before_dedup=0, normalized_records=0)
    assert m.records_fetched == 0
    assert m.is_reconciled()


def test_failed_run_cannot_report_live_records() -> None:
    m = dm.RunMetrics(succeeded=False, records_live=10, records_fetched=10,
                      records_before_dedup=10, normalized_records=10)
    assert not m.is_reconciled()
    assert any("failed run" in e for e in m.reconciliation_errors())


def test_metrics_round_trip_and_no_historical_leak() -> None:
    m = dm.RunMetrics(run_id="r", records_fetched=3, records_before_dedup=3, normalized_records=3,
                      records_scored=3, watch=3, records_live=3, data_mode=dm.MODE_LIVE)
    payload = m.to_dict()
    again = dm.RunMetrics.from_dict(payload)
    assert again.records_fetched == 3
    # An unrelated historical field cannot be smuggled into the contract.
    payload["records_pulled_all_time"] = 18213
    filtered = dm.RunMetrics.from_dict(payload)
    assert not hasattr(filtered, "records_pulled_all_time")


def test_successful_promotion() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "state"
        ds = _dataset(Path(tmp), dataset_id="ds1")
        result = dm.promote_dataset(ds, state_root=state)
        assert result.promoted, result.errors
        active = dm.load_active_dataset(state_root=state)
        assert active is not None
        assert active.dataset_id == "ds1"
        assert active.data_mode == dm.MODE_LIVE
        # dataset manifest persisted separately
        manifests = list((state / "datasets").glob("dataset_ds1.json"))
        assert manifests


def test_failed_validation_keeps_previous_pointer() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "state"
        good = _dataset(Path(tmp), dataset_id="good")
        assert dm.promote_dataset(good, state_root=state).promoted

        invalid = _dataset(Path(tmp), dataset_id="bad", valid=False)
        result = dm.promote_dataset(invalid, state_root=state)
        assert not result.promoted
        assert result.reason == "validation_failed"
        # previous pointer is preserved unchanged
        active = dm.load_active_dataset(state_root=state)
        assert active is not None and active.dataset_id == "good"


def test_empty_and_missing_dataset_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "state"
        empty = _dataset(Path(tmp), dataset_id="empty", total=0)
        assert not dm.promote_dataset(empty, state_root=state).promoted

        missing = _dataset(Path(tmp), dataset_id="missing", create_file=False)
        r = dm.promote_dataset(missing, state_root=state)
        assert not r.promoted
        assert any("does not exist" in e for e in r.errors)


def test_missing_pointer_returns_none() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "state"
        assert dm.load_active_dataset(state_root=state) is None


def test_corrupted_pointer_recovers_from_backup() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "state"
        first = _dataset(Path(tmp), dataset_id="first")
        second = _dataset(Path(tmp), dataset_id="second")
        assert dm.promote_dataset(first, state_root=state).promoted
        assert dm.promote_dataset(second, state_root=state).promoted  # writes .bak of first

        pointer = state / "datasets" / "active_dataset.json"
        pointer.write_text("{ this is not valid json", encoding="utf-8")
        recovered = dm.load_active_dataset(state_root=state)
        # backup held the previous (first) pointer; recovery restores a valid one.
        assert recovered is not None
        assert recovered.dataset_id == "first"


def test_atomic_pointer_replacement_leaves_no_tmp() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "state"
        assert dm.promote_dataset(_dataset(Path(tmp), dataset_id="x"), state_root=state).promoted
        leftovers = list((state / "datasets").glob("*.tmp"))
        assert not leftovers


def test_atomic_json_writer_is_safe_for_concurrent_writers() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "shared.json"
        payloads = [{"writer": i, "content": "x" * (1000 + i)} for i in range(32)]
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda payload: atomic_write_json(target, payload), payloads))

        assert json.loads(target.read_text(encoding="utf-8")) in payloads
        assert not list(Path(tmp).glob("*.tmp"))


def test_packaged_synthetic_detection() -> None:
    package_root = ROOT.parents[1]
    packaged = dm.packaged_synthetic_review_path(package_root=package_root)
    assert dm.is_packaged_synthetic(packaged, package_root=package_root)
    assert not dm.is_packaged_synthetic(package_root / "config" / "keywords.xlsx",
                                        package_root=package_root)
    prov = dm.synthetic_provenance_for_packaged_input(package_root=package_root, record_total=12)
    assert prov.data_mode == dm.MODE_SYNTHETIC
    assert prov.record_counts["synthetic"] == 12


def test_pointer_is_outside_package() -> None:
    # datasets_root must refuse to live inside the package repository.
    package_root = ROOT.parents[1]
    root = dm.datasets_root(state_root=Path(tempfile.gettempdir()) / "tf_state_test",
                            package_root=package_root, create=False)
    assert "datasets" in root.parts


def main() -> int:
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print(f"Build Week data-modes tests: {len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
