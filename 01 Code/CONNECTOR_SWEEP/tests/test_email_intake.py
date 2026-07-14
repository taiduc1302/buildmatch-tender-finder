from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tenderfinder_email_intake import parse_eml_dir


def main() -> int:
    fixtures = Path(__file__).resolve().parent / "fixtures" / "email_alerts"
    rows = parse_eml_dir(fixtures)
    assert len(rows) == 5, f"expected 5 deduped rows, got {len(rows)}"

    civil_open = [r for r in rows if "105A Avenue" in r.tender_title]
    assert len(civil_open) == 1, "duplicate civil open alert was not deduped"
    assert civil_open[0].civil_relevant is True, "civil open alert should score YES"
    assert civil_open[0].status == "open", f"civil open status wrong: {civil_open[0].status}"

    non_civil = [r for r in rows if "Furniture" in r.tender_title]
    assert len(non_civil) == 1, "non-civil fixture missing"
    assert non_civil[0].civil_relevant is False, "non-civil fixture should score NO"

    expired = [r for r in rows if "Drainage Culvert" in r.tender_title]
    assert len(expired) == 1, "expired fixture missing"
    assert expired[0].civil_relevant is True, "expired civil fixture should score YES"
    assert expired[0].status == "closed", f"expired fixture should be closed, got {expired[0].status}"
    assert expired[0].tender_title == "Drainage Culvert Replacement"

    html_row = [r for r in rows if "Fraser Valley Utility Corridor Upgrade" in r.tender_title]
    assert len(html_row) == 1, "base64/html fixture missing"
    assert html_row[0].parse_confidence in {"high", "medium"}
    assert "example.com/tenders/fvrd-utility-corridor" in html_row[0].url
    assert html_row[0].found_via == "email_tracking_link"

    bidcentral = [r for r in rows if "Kelowna Pump Station Upgrade" in r.tender_title]
    assert len(bidcentral) == 1, "BidCentral fixture missing"
    assert bidcentral[0].provider == "bidcentral.ca"
    assert bidcentral[0].civil_relevant is True

    print("Email intake fixture tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
