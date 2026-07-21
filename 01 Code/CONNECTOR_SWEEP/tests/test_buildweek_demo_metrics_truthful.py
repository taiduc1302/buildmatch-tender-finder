"""Regression test: a demo/report build must never report the historical
BASELINE constants (e.g. the old "27,260 records pulled live" figure) as
this run's live-fetch metrics. ``read_track_a`` must always trust the
current run's ``TENDER_FINDER_Run_Source_Summary.csv`` over the DemoData
dataclass's hardcoded historical defaults, including a truthful zero for an
offline / ``--no-fetch`` run.

Runs both under pytest and as a plain ``python
test_buildweek_demo_metrics_truthful.py`` script (so the offline Self-Test
can invoke it).
"""
from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tenderfinder_demo_three_buckets as demo  # noqa: E402


def _write_empty_review_workbook(path: Path) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["source_id", "app_no", "route", "fit_score", "municipality", "address"])
    wb.save(path)


def _write_source_summary(path: Path, rows: list[dict]) -> None:
    fieldnames = ["source_id", "records_pulled", "records_normalized"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_no_fetch_run_reports_zero_not_the_historical_baseline() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        review_xlsx = tmp_path / "review.xlsx"
        _write_empty_review_workbook(review_xlsx)
        _write_source_summary(
            tmp_path / "TENDER_FINDER_Run_Source_Summary.csv",
            [
                {"source_id": "bc_bid_public", "records_pulled": 0, "records_normalized": 0},
                {"source_id": "fvrd_tenders", "records_pulled": 0, "records_normalized": 0},
            ],
        )
        data = demo.read_track_a(review_xlsx)

    assert data.records_pulled == 0  # not BASELINE["records_pulled"] == 27260
    assert data.records_normalized == 0  # not BASELINE["records_normalized"] == 19146
    assert data.live_sources == 0  # not BASELINE["working_sources"] == 5
    assert data.coded_sources == 2


def test_no_fetch_run_is_truthful_even_without_a_source_summary_file() -> None:
    """The real offline demo path reads a static, checked-in "proven" review
    workbook that has NO sibling TENDER_FINDER_Run_Source_Summary.csv at
    all (it is not the output of a fresh sweep). Without the ``no_fetch``
    override, DemoData's dataclass field defaults (the historical BASELINE
    constants, e.g. 27,260) leak straight through untouched. A --no-fetch
    run must report 0 live-fetched records regardless."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        review_xlsx = tmp_path / "review.xlsx"
        _write_empty_review_workbook(review_xlsx)
        # deliberately no TENDER_FINDER_Run_Source_Summary.csv written here
        data = demo.read_track_a(review_xlsx, no_fetch=True)

    assert data.records_pulled == 0  # not BASELINE["records_pulled"] == 27260
    assert data.live_sources == 0  # not BASELINE["working_sources"] == 5


def test_fetch_run_without_summary_file_keeps_legacy_baseline_behavior() -> None:
    """Sanity check: the no_fetch override is opt-in. A caller that does not
    pass ``no_fetch=True`` (i.e. not an offline/no-fetch run) keeps the
    pre-existing behavior when no current-run summary is available."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        review_xlsx = tmp_path / "review.xlsx"
        _write_empty_review_workbook(review_xlsx)
        data = demo.read_track_a(review_xlsx)

    assert data.records_pulled == demo.BASELINE["records_pulled"]


def test_live_run_still_reports_actual_current_run_counts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        review_xlsx = tmp_path / "review.xlsx"
        _write_empty_review_workbook(review_xlsx)
        _write_source_summary(
            tmp_path / "TENDER_FINDER_Run_Source_Summary.csv",
            [
                {"source_id": "bc_bid_public", "records_pulled": 12, "records_normalized": 9},
                {"source_id": "fvrd_tenders", "records_pulled": 3, "records_normalized": 3},
            ],
        )
        data = demo.read_track_a(review_xlsx)

    assert data.records_pulled == 15  # actual measured value, not the baseline default
    assert data.records_normalized == 12
    assert data.live_sources == 2
    assert data.coded_sources == 2


def main() -> int:
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print(f"Build Week demo-metrics truthfulness tests: {len(tests)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
