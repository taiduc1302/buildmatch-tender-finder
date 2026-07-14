from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tenderfinder_demo_three_buckets import protected_sha_status  # noqa: E402
from tenderfinder_email_intake import parse_eml_dir  # noqa: E402


def test_protected_sha_status_missing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        status, sha = protected_sha_status(Path(tmp) / "missing.xlsx", "abc123")
        assert status == "NOT_AVAILABLE"
        assert sha == "NOT_AVAILABLE"


def test_email_fixture_titles_are_clean() -> None:
    fixtures = Path(__file__).resolve().parent / "fixtures" / "email_alerts"
    rows = parse_eml_dir(fixtures)
    titles = {row.tender_title for row in rows}
    assert "Fraser Valley Utility Corridor Upgrade" in titles
    assert "Kelowna Pump Station Upgrade" in titles
    assert "Drainage Culvert Replacement" in titles
    assert all("Daily Matches" not in title for title in titles)
    assert all("Daily Notification" not in title for title in titles)
    assert all("BC Bid Alert" not in title for title in titles)


def test_tracking_links_are_labeled_when_unwrapped() -> None:
    fixtures = Path(__file__).resolve().parent / "fixtures" / "email_alerts"
    rows = parse_eml_dir(fixtures)
    tracking_row = next(row for row in rows if row.tender_title == "Fraser Valley Utility Corridor Upgrade")
    assert tracking_row.url == "https://example.com/tenders/fvrd-utility-corridor"
    assert tracking_row.found_via == "email_tracking_link"


def test_source_text_has_no_stale_patch_57_talktrack_or_old_email_summary() -> None:
    source = (ROOT / "tenderfinder_demo_three_buckets.py").read_text(encoding="utf-8")
    assert "Patch 5.7 built and deployed the email alert intake module." not in source
    assert "Email intake kept in BID NOW:" not in source
    assert '["x] Protected master SHA values unchanged' not in source


def main() -> int:
    tests = [
        test_protected_sha_status_missing,
        test_email_fixture_titles_are_clean,
        test_tracking_links_are_labeled_when_unwrapped,
        test_source_text_has_no_stale_patch_57_talktrack_or_old_email_summary,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print("Patch 5.23 output consistency tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
