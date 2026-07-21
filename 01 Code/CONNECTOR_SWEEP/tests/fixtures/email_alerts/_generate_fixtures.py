"""Deterministically regenerate the synthetic email-alert fixtures.

These ``.eml`` files are entirely fictitious, sanitized samples used to test
the offline email-intake parser. They contain no real inbox content, no real
recipients, and no secrets. Every URL points at ``example.com`` (a reserved
documentation domain) except the deliberately-crafted SendGrid-style tracking
wrapper, whose embedded target is also ``example.com``.

Run ``python _generate_fixtures.py`` from this directory to rewrite the six
``.eml`` files byte-for-byte. Test expectations that depend on these fixtures:

* ``tests/test_patch_523_output_consistency.py`` — clean titles + unwrapped
  tracking link (``email_tracking_link``).
* ``tests/test_email_intake.py`` — 5 deduped rows, civil/non-civil/closed mix.
* ``tests/test_email_intake_provider_neutral.py`` — per-provider counts.
* ``tests/test_email_import_folder_ux.py`` — >= 6 alert emails present.
"""
from __future__ import annotations

from email.generator import BytesGenerator
from email.message import EmailMessage
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _write(name: str, msg: EmailMessage) -> None:
    with (HERE / name).open("wb") as handle:
        BytesGenerator(handle).flatten(msg)


def _plain(name: str, sender: str, subject: str, body: str, msg_id: str, date: str) -> None:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = "estimating@example.com"
    msg["Subject"] = subject
    msg["Message-ID"] = msg_id
    msg["Date"] = date
    msg.set_content(body)
    _write(name, msg)


def main() -> int:
    # 1 + 2: duplicate civil OPEN alert (same title, no url, no closing date ->
    # deduped to a single row; status defaults to open).
    body_105a = (
        "A new opportunity matched your saved civil search.\n\n"
        "Project: 105A Avenue Water Feeder and Distribution Main Improvements\n"
        "Scope: Installation of a new water feeder main and distribution water "
        "main, including trench, watermain tie-ins and road restoration.\n"
        "Location: Surrey, BC\n"
        "Category: Civil / Underground Utilities\n"
    )
    _plain(
        "fixture_01_105a_avenue_bidsandtenders.eml",
        "TENDER Alerts <alerts@bidsandtenders.ca>",
        "Daily Notification: 105A Avenue Water Feeder and Distribution Main Improvements",
        body_105a,
        "<fixture-105a-1@example.com>",
        "Sat, 18 Jul 2026 08:00:00 -0700",
    )
    _plain(
        "fixture_02_105a_avenue_duplicate_bidsandtenders.eml",
        "TENDER Alerts <alerts@bidsandtenders.ca>",
        "Daily Notification: 105A Avenue Water Feeder and Distribution Main Improvements",
        body_105a,
        "<fixture-105a-2@example.com>",
        "Sat, 18 Jul 2026 09:15:00 -0700",
    )

    # 3: non-civil goods alert (must score civil_relevant = False).
    _plain(
        "fixture_03_office_furniture_noncivil_bidsandtenders.eml",
        "TENDER Alerts <alerts@bidsandtenders.ca>",
        "BC Bid Alert: Office Furniture Supply and Delivery",
        "Opportunity type: Goods.\n"
        "Category: Office furnishings.\n"
        "Supply and delivery of modular office desks, task chairs and shelving "
        "for a municipal administration building.\n",
        "<fixture-furniture@example.com>",
        "Sat, 18 Jul 2026 10:05:00 -0700",
    )

    # 4: civil CLOSED alert (explicit closed status keeps it date-durable).
    _plain(
        "fixture_04_drainage_culvert_closed_bidcentral.eml",
        "BidCentral Notifications <notifications@bidcentral.ca>",
        "Daily Matches - BidCentral - Drainage Culvert Replacement",
        "Status: Closed. This opportunity has closed and is shown for reference.\n"
        "Project: Drainage Culvert Replacement\n"
        "Scope: Removal and replacement of a failed storm drainage culvert, "
        "including excavation and road reinstatement.\n",
        "<fixture-drainage@example.com>",
        "Fri, 10 Jul 2026 14:00:00 -0700",
    )

    # 5: HTML alert with a SendGrid-style tracking wrapper (base64 body).
    tracking = (
        "https://links.sendgrid.net/wf/click?"
        "url=https%3A%2F%2Fexample.com%2Ftenders%2Ffvrd-utility-corridor"
        "&rid=ab12cd34"
    )
    html = (
        "<html><body>"
        "<h2>Fraser Valley Utility Corridor Upgrade</h2>"
        "<p>A new civil opportunity matched your saved search: a utility "
        "corridor upgrade including watermain, sanitary and storm sewer works.</p>"
        f'<p><a href="{tracking}">View this opportunity</a></p>'
        '<p><a href="https://links.sendgrid.net/wf/click?url=https%3A%2F%2Fexample.com%2Funsubscribe">Unsubscribe</a></p>'
        "</body></html>"
    )
    msg = EmailMessage()
    msg["From"] = "BC Bid <donotreply@bcbid.gov.bc.ca>"
    msg["To"] = "estimating@example.com"
    msg["Subject"] = "BC Bid Alert: Fraser Valley Utility Corridor Upgrade"
    msg["Message-ID"] = "<fixture-fvrd@example.com>"
    msg["Date"] = "Sat, 18 Jul 2026 07:30:00 -0700"
    msg.set_content("Fraser Valley Utility Corridor Upgrade. View the opportunity online.")
    # base64-encode the HTML part (cte) so the decode path is exercised.
    msg.add_alternative(html, subtype="html", cte="base64")
    _write("fixture_05_fvrd_utility_corridor_html_bcbid.eml", msg)

    # 6: civil OPEN alert from BidCentral (provider assertion).
    _plain(
        "fixture_06_kelowna_pump_station_bidcentral.eml",
        "BidCentral Notifications <notifications@bidcentral.ca>",
        "BidCentral - Kelowna Pump Station Upgrade",
        "Project: Kelowna Pump Station Upgrade\n"
        "Scope: Upgrade of a sanitary sewer pump station including new forcemain "
        "and site servicing.\n"
        "Category: Civil / Utilities\n",
        "<fixture-kelowna@example.com>",
        "Sat, 18 Jul 2026 11:20:00 -0700",
    )
    print("Wrote 6 email-alert fixtures to", HERE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
