from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tenderfinder_demo_three_buckets import (  # noqa: E402
    DemoData,
    build_developer_rows,
    classify_applicant_name,
    stable_lead_id,
)


def make_row(applicant_name: str, app_no: str, units: int = 120) -> dict:
    row = {
        "municipality": "Coquitlam",
        "app_no": app_no,
        "address": f"{app_no} Test Avenue",
        "source": "Unit Test",
        "source_id": "unit_test",
        "fit_score": 70,
        "signal_quality": "HIGH",
        "scope_summary": f"{units} residential units",
        "est_units": units,
        "applicant_name": applicant_name,
    }
    row["lead_id"] = stable_lead_id(row)
    return row


def main() -> int:
    consultant_examples = [
        "Sam Example DBA: Camphora Engineering",
        "Dana Example DBA: LMDG Building Code Consultants Ltd.",
        "Morgan Example DBA: LMDG Building Code Consultant",
        "Bobby Example DBA: Certified Professional",
        "Taylor Example DBA: McAuley Consulting",
        "Chris Dikeakos Architects Inc.",
        "Mel Example DBA: Jensen Hughes",
    ]
    for name in consultant_examples:
        assert classify_applicant_name(name, est_units=500) == "DESIGN_CONSULTANT", name

    for name in ["Beedie Fraser Mills LP", "Polygon Development 311 Ltd.", "Anthem Properties"]:
        assert classify_applicant_name(name, est_units=0) == "DEVELOPER", name

    data = DemoData()
    data.future = [
        make_row("Dana Example DBA: LMDG Building Code Consultants Ltd.", "LMDG-1"),
        make_row("Morgan Example DBA: LMDG Building Code Consultant", "LMDG-2"),
        make_row("Polygon Development 311 Ltd.", "POLY-1"),
        make_row("Polygon Beaumont Homes Ltd.", "POLY-2"),
        make_row("Polygon Coronation Heights Homes Ltd.", "POLY-3"),
    ]
    dev_rows, consultant_rows = build_developer_rows(data)
    consultant_names = {row["applicant_name"] for row in consultant_rows}
    developer_names = {row["applicant_name"] for row in dev_rows}
    assert "LMDG Building Code Consultants" in consultant_names
    assert "Polygon" in developer_names
    lmdg = next(row for row in consultant_rows if row["applicant_name"] == "LMDG Building Code Consultants")
    assert lmdg["total_applications"] == 2
    assert lmdg["applicant_type"] == "DESIGN_CONSULTANT"

    print("Developer classification test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
