from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tenderfinder_demo_three_buckets import (  # noqa: E402
    apply_status_date_fallback,
    extract_surrey_tender_fields,
    infer_status,
)


def surrey_block(status: str, closing: str, extra: str = "") -> str:
    return f"""
    <html><body>
      <nav>Closed tenders archive Careers Maps Search</nav>
      <h1>{extra}</h1>
      <div class="flex-content__item flex-content__item--block">
        <h4>Status</h4>
        <p><strong>{status}</strong></p>
      </div>
      <div class="flex-content__item flex-content__item--block">
        <h4>Closing Date</h4>
        <div class="field field--name-field-tender-closing-date field__item">{closing}</div>
      </div>
    </body></html>
    """


def test_105a_avenue_water_feeder_open() -> None:
    status, closing = extract_surrey_tender_fields(surrey_block(
        "Open",
        "July 9, 2026 - 2:00pm local time",
        "105A Avenue Water Feeder and Distribution Main Improvements",
    ))
    assert status == "open"
    assert closing == "2026-07-09"


def test_road_utility_10975_126a_open() -> None:
    status, closing = extract_surrey_tender_fields(surrey_block(
        "Open",
        "July 13, 2026 - 2:00pm local time",
        "Road and Utility Site Servicing Work at 10975-126A Street",
    ))
    assert status == "open"
    assert closing == "2026-07-13"


def test_trench_shield_open_preferred_quotation_date() -> None:
    status, closing = extract_surrey_tender_fields(surrey_block(
        "Open",
        "The City would prefer to receive Quotations on or before July 6, 2026",
        "Supply and Delivery of Two Trench Shield System",
    ))
    assert status == "open"
    assert closing == "2026-07-06"


def test_future_date_without_explicit_status_is_not_closed() -> None:
    # Use a genuinely future closing date computed at run time so the test
    # keeps asserting the intended behaviour (a future date with only the
    # boilerplate "Closed tenders archive" nav text must not be treated as a
    # closed tender) instead of decaying into a stale hardcoded date.
    future = dt.date.today() + dt.timedelta(days=120)
    future_human = f"{future.strftime('%B')} {future.day}, {future.year}"
    status, closing = infer_status(
        f"Closed tenders archive Closing Date {future_human} watermain sanitary sewer"
    )
    assert closing == future.isoformat()
    assert apply_status_date_fallback(status, closing) == "open_or_needs_review"


def main() -> int:
    tests = [
        test_105a_avenue_water_feeder_open,
        test_road_utility_10975_126a_open,
        test_trench_shield_open_preferred_quotation_date,
        test_future_date_without_explicit_status_is_not_closed,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print("Surrey tender status parser test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
