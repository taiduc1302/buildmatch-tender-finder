"""Tests for the headless development-data refresh orchestration (Phase 2).

Uses injected fake acquirer/scorer so the full flow runs headlessly with no
network and no real workbook engine. Runs under pytest and as a script.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPO_ROOT = ROOT.parents[1]

import tenderfinder_refresh_service as rs  # noqa: E402
import tenderfinder_data_modes as dm  # noqa: E402


def _records(source_id: str, n: int) -> tuple[dict, ...]:
    return tuple(
        {
            "source": source_id,
            "app_no": f"{source_id}-{i}",
            "address": f"{100 + i} Example St",
            "scope_summary": "New multi-lot subdivision servicing with watermain and storm sewer",
            "app_type_stage": "Development Permit",
            "municipality": "Surrey",
        }
        for i in range(n)
    )


def _ok_acquirer(source):
    return rs.SourceFetch(source_id=source["source_id"], ok=True, records=_records(source["source_id"], 3),
                          http_status=200)


def _fake_scorer(dataset_path: Path, out_dir: Path) -> rs.ScoreResult:
    out = out_dir / "ranked.xlsx"
    out.write_bytes(b"PK\x03\x04 fake ranked workbook")
    return rs.ScoreResult(output_path=str(out), scored=9, bid_now=1, bid_later=3, watch=2, skip=3)


def test_eligible_sources_exclude_non_runnable() -> None:
    eligible = rs.eligible_development_sources(package_root=REPO_ROOT)
    ids = {s["source_id"] for s in eligible}
    # needs_configuration / manual_only / wrong_source sources must be excluded
    for excluded in ("van_rezoning", "van_devpermits", "city_langley_devapps", "burnaby_devapps"):
        assert excluded not in ids, f"{excluded} must not be runnable"
    # a known ready development source is present
    assert any(s["operational_status"] in ("ready_for_live_test", "verified_live") for s in eligible)


def test_source_health_never_marks_failed_source_healthy() -> None:
    health = rs.source_health_rows(package_root=REPO_ROOT, track="development")
    by_id = {row["source_id"]: row for row in health}
    van = by_id.get("van_rezoning")
    assert van is not None
    assert van["runtime_eligible"] is False
    assert van["skip_reason"]


def test_full_refresh_flow_promotes_scores_and_writes_manifest() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "state"
        result = rs.refresh_development_data(
            rs.RefreshRequest(preset_id="civil_contractor", state_root=state, package_root=REPO_ROOT,
                              source_ids=("maple_ridge_devapps", "twp_langley_devactivity")),
            acquirer=_ok_acquirer, scorer=_fake_scorer,
        )
        assert result.succeeded, result.message
        # active pointer set to the new live dataset
        active = dm.load_active_dataset(state_root=state, package_root=REPO_ROOT)
        assert active is not None and active.data_mode == dm.MODE_LIVE
        # metrics reconcile and are truthful
        assert result.metrics.is_reconciled(), result.metrics.reconciliation_errors()
        assert result.metrics.records_fetched == 6
        assert result.metrics.records_scored == 9
        assert result.metrics.data_mode == dm.MODE_LIVE
        # output + manifest written
        assert Path(result.output_paths["output_workbook"]).exists()
        assert Path(result.manifest_path).exists()


def test_partial_source_failure_still_produces_dataset() -> None:
    def flaky(source):
        if source["source_id"].startswith("maple"):
            return rs.SourceFetch(source_id=source["source_id"], ok=False, error="503 upstream")
        return _ok_acquirer(source)

    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "state"
        result = rs.refresh_development_data(
            rs.RefreshRequest(state_root=state, package_root=REPO_ROOT,
                              source_ids=("maple_ridge_devapps", "twp_langley_devactivity")),
            acquirer=flaky, scorer=_fake_scorer,
        )
        assert result.succeeded
        assert result.metrics.sources_failed == 1
        assert result.metrics.sources_successful == 1
        outcomes = {o["source_id"]: o for o in result.source_outcomes}
        assert outcomes["maple_ridge_devapps"]["ok"] is False


def test_total_failure_preserves_previous_dataset_and_marks_stale() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "state"
        # first, a good refresh establishes a live dataset
        good = rs.refresh_development_data(
            rs.RefreshRequest(state_root=state, package_root=REPO_ROOT,
                              source_ids=("maple_ridge_devapps",)),
            acquirer=_ok_acquirer, scorer=_fake_scorer,
        )
        assert good.succeeded
        good_dataset_id = dm.load_active_dataset(state_root=state, package_root=REPO_ROOT).dataset_id

        # now every source fails
        def all_fail(source):
            return rs.SourceFetch(source_id=source["source_id"], ok=False, error="network down")

        failed = rs.refresh_development_data(
            rs.RefreshRequest(state_root=state, package_root=REPO_ROOT,
                              source_ids=("maple_ridge_devapps", "twp_langley_devactivity")),
            acquirer=all_fail, scorer=_fake_scorer,
        )
        assert not failed.succeeded
        assert failed.stale
        # previous active dataset is unchanged (not overwritten by the failed run)
        still = dm.load_active_dataset(state_root=state, package_root=REPO_ROOT)
        assert still.dataset_id == good_dataset_id
        assert still.data_mode == dm.MODE_LIVE  # pointer itself untouched
        # the failure result labels continued use as cached/stale
        assert failed.provenance is not None and failed.provenance.stale
        assert failed.metrics.succeeded is False
        assert not failed.metrics.records_live  # a failed run reports no live records


def test_failed_validation_preserves_previous() -> None:
    def empty_records(source):
        # ok but returns records with no descriptive field -> validation fails
        return rs.SourceFetch(source_id=source["source_id"], ok=True,
                              records=({"source": source["source_id"], "app_no": "x"},))

    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "state"
        result = rs.refresh_development_data(
            rs.RefreshRequest(state_root=state, package_root=REPO_ROOT,
                              source_ids=("maple_ridge_devapps",)),
            acquirer=empty_records, scorer=_fake_scorer,
        )
        assert not result.succeeded
        assert dm.load_active_dataset(state_root=state, package_root=REPO_ROOT) is None


def test_dedup_reconciles() -> None:
    dupes = [
        {"source": "s", "app_no": "1", "address": "1 St", "scope_summary": "civil"},
        {"source": "s", "app_no": "1", "address": "1 St", "scope_summary": "civil"},
        {"source": "s", "app_no": "2", "address": "2 St", "scope_summary": "civil"},
    ]
    deduped, removed = rs.deduplicate_records(dupes)
    assert len(deduped) == 2 and removed == 1


def test_never_writes_inside_package() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "state"
        result = rs.refresh_development_data(
            rs.RefreshRequest(state_root=state, package_root=REPO_ROOT,
                              source_ids=("maple_ridge_devapps",)),
            acquirer=_ok_acquirer, scorer=_fake_scorer,
        )
        dataset_path = Path(result.output_paths["dataset"]).resolve()
        assert str(REPO_ROOT.resolve()) not in str(dataset_path)


# --------------------------------------------------------------------------- #
# Full-sweep acquirer (Gap A fix): must NOT be the bounded connector preview.
# tenderfinder_raw_sweep.run_connector is monkeypatched so these tests remain
# fully offline/deterministic — no real network I/O in the mandatory suite.
# --------------------------------------------------------------------------- #


def _fake_lead(project_id="P1", municipality="Surrey", app_no="A1", address="1 Main St",
               owner="Acme Developer", app_type_stage="Development Permit",
               scope_summary="Watermain and sanitary sewer servicing", fit_score=82,
               source_url="https://example.com/p1", proposed_route="Future_Projects"):
    return {
        "project_id": project_id, "municipality": municipality, "app_no": app_no,
        "address": address, "owner": owner, "app_type_stage": app_type_stage,
        "scope_summary": scope_summary, "fit_score": fit_score, "source_url": source_url,
        "proposed_route": proposed_route, "date_found": "2026-07-19", "raw_hash": "abc123",
        "dedupe_key": f"{app_no}|{address}",
    }


def _source_row(source_id="maple_ridge_devapps"):
    rows = rs.eligible_development_sources(package_root=REPO_ROOT, source_ids=(source_id,))
    assert rows, f"{source_id} must be a runtime-eligible fixture for this test"
    return rows[0]


def test_full_sweep_acquirer_maps_many_leads_not_a_bounded_preview() -> None:
    import tenderfinder_raw_sweep as raw_sweep

    many_leads = [_fake_lead(project_id=f"P{i}", app_no=f"A{i}", address=f"{i} Main St")
                  for i in range(37)]  # far more than a ~5-record preview
    original = raw_sweep.run_connector

    def fake_run_connector(conn, max_records, probe=False, raw_dir=None, **kwargs):
        assert probe is False
        return {"status": "load_ok", "error": "", "leads": many_leads[:max_records],
                "records_pulled": len(many_leads), "http_status": 200}

    raw_sweep.run_connector = fake_run_connector
    try:
        fetch = rs.full_sweep_development_acquirer(_source_row(), max_records=500)
    finally:
        raw_sweep.run_connector = original

    assert fetch.ok
    assert fetch.count == 37  # NOT bounded to a small preview sample
    assert fetch.records[0]["scope_summary"] == "Watermain and sanitary sewer servicing"
    assert fetch.records[0]["app_no"] == "A0"


def test_full_sweep_acquirer_respects_max_records_cap() -> None:
    import tenderfinder_raw_sweep as raw_sweep

    captured = {}
    original = raw_sweep.run_connector

    def fake_run_connector(conn, max_records, probe=False, raw_dir=None, **kwargs):
        captured["max_records"] = max_records
        return {"status": "load_ok", "error": "", "leads": [], "http_status": 200}

    raw_sweep.run_connector = fake_run_connector
    try:
        rs.full_sweep_development_acquirer(_source_row(), max_records=250)
    finally:
        raw_sweep.run_connector = original
    assert captured["max_records"] == 250


def test_full_sweep_acquirer_non_fetch_status_is_not_ok() -> None:
    import tenderfinder_raw_sweep as raw_sweep

    original = raw_sweep.run_connector
    raw_sweep.run_connector = lambda conn, max_records, probe=False, raw_dir=None, **kw: {
        "status": "access_test_required", "error": "", "leads": [], "http_status": 0,
    }
    try:
        fetch = rs.full_sweep_development_acquirer(_source_row(), max_records=100)
    finally:
        raw_sweep.run_connector = original
    assert not fetch.ok
    assert "access_test_required" in fetch.error


def test_full_sweep_acquirer_error_is_not_ok() -> None:
    import tenderfinder_raw_sweep as raw_sweep

    original = raw_sweep.run_connector
    raw_sweep.run_connector = lambda conn, max_records, probe=False, raw_dir=None, **kw: {
        "status": "load_error", "error": "504 Gateway Timeout", "leads": [], "http_status": 504,
    }
    try:
        fetch = rs.full_sweep_development_acquirer(_source_row(), max_records=100)
    finally:
        raw_sweep.run_connector = original
    assert not fetch.ok
    assert "504" in fetch.error


def test_full_sweep_acquirer_exception_is_a_failed_source_not_a_crash() -> None:
    import tenderfinder_raw_sweep as raw_sweep

    original = raw_sweep.run_connector

    def boom(*a, **k):
        raise RuntimeError("network unreachable")

    raw_sweep.run_connector = boom
    try:
        fetch = rs.full_sweep_development_acquirer(_source_row(), max_records=100)
    finally:
        raw_sweep.run_connector = original
    assert not fetch.ok
    assert "network unreachable" in fetch.error


def test_make_full_sweep_acquirer_binds_raw_dir_outside_package() -> None:
    import tenderfinder_raw_sweep as raw_sweep

    captured = {}
    original = raw_sweep.run_connector
    raw_sweep.run_connector = lambda conn, max_records, probe=False, raw_dir=None, **kw: (
        captured.__setitem__("raw_dir", raw_dir) or
        {"status": "load_ok", "error": "", "leads": [], "http_status": 200}
    )
    try:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            request = rs.RefreshRequest(state_root=state, package_root=REPO_ROOT, run_id="run123")
            acquirer = rs.make_full_sweep_acquirer(request, package_root=REPO_ROOT, run_id="run123")
            acquirer(_source_row())
    finally:
        raw_sweep.run_connector = original
    assert captured["raw_dir"] is not None
    assert str(REPO_ROOT.resolve()) not in str(captured["raw_dir"])
    assert "run123" in str(captured["raw_dir"])


def test_full_sweep_flow_promotes_dataset_with_many_records() -> None:
    """End-to-end: full-sweep acquirer feeding the whole promote/score pipeline
    with a realistically large per-source count (not a tiny preview)."""
    import tenderfinder_raw_sweep as raw_sweep

    many_leads = [_fake_lead(project_id=f"P{i}", app_no=f"A{i}", address=f"{i} Main St")
                  for i in range(150)]
    original = raw_sweep.run_connector
    raw_sweep.run_connector = lambda conn, max_records, probe=False, raw_dir=None, **kw: {
        "status": "load_ok", "error": "", "leads": many_leads[:max_records], "http_status": 200,
    }
    try:
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state"
            run_id = "run_full_sweep_e2e"
            request = rs.RefreshRequest(
                state_root=state, package_root=REPO_ROOT, run_id=run_id,
                source_ids=("maple_ridge_devapps",), max_records_per_source=500,
            )
            acquirer = rs.make_full_sweep_acquirer(request, package_root=REPO_ROOT, run_id=run_id)
            result = rs.refresh_development_data(request, acquirer=acquirer, scorer=_fake_scorer)

            assert result.succeeded, result.message
            assert result.metrics.records_fetched == 150  # far above a ~5-record preview
            assert result.metrics.normalized_records == 150
            active = dm.load_active_dataset(state_root=state, package_root=REPO_ROOT)
            assert active is not None and active.record_counts["total"] == 150
    finally:
        raw_sweep.run_connector = original


def test_diagnostic_preview_and_full_sweep_are_distinct_functions() -> None:
    # Guards against accidentally re-aliasing the bounded preview back onto the
    # production entry point (the original Gap A defect).
    assert rs.full_sweep_development_acquirer is not rs.diagnostic_preview_acquirer
    assert rs.default_development_acquirer is rs.diagnostic_preview_acquirer


def main() -> int:
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print(f"Build Week refresh-service tests: {len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
