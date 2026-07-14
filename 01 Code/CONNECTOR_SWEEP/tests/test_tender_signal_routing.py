from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tenderfinder_demo_three_buckets import (  # noqa: E402
    email_tender_to_candidate,
    SourceLog,
    TenderCandidate,
    finalize_tender_signals,
    infer_source_type,
    is_real_opportunity_candidate,
)
from tenderfinder_email_intake import EmailTender  # noqa: E402


def main() -> int:
    tenders = [
        TenderCandidate("surrey", "Surrey", "Open Tender", "https://example.com/open", True, "open", "public"),
        TenderCandidate("surrey", "Surrey", "Closed Tender", "https://example.com/closed", True, "closed", "public"),
        TenderCandidate("richmond", "Richmond", "Historical Tender", "https://example.com/hist", False, "historical archive", "public"),
    ]
    logs = [
        SourceLog("surrey", "Surrey", "https://example.com", "OK_HTML", source_type=infer_source_type("surrey", "https://example.com")),
        SourceLog("richmond", "Richmond", "https://example.com", "OK_HTML", source_type=infer_source_type("richmond", "https://example.com")),
        SourceLog("blocked", "Blocked Source", "https://example.com", "FORBIDDEN_BUT_LIKELY_VALID", source_type=infer_source_type("blocked", "https://example.com")),
        SourceLog("portal", "Portal Source", "https://bidsandtenders.ca", "SKIPPED_LOGIN_PLATFORM", source_type=infer_source_type("portal", "https://bidsandtenders.ca")),
        SourceLog("paid", "Paid Source", "https://www.bidcentral.ca", "LANDING_ONLY_MEMBERSHIP_LIKELY", source_type=infer_source_type("paid", "https://www.bidcentral.ca"), note="Landing page only; membership likely required."),
        SourceLog("parsezero", "Parse Zero", "https://example.com/empty", "OK_HTML", source_type=infer_source_type("parsezero", "https://example.com/empty")),
        SourceLog("historyonly", "History Only", "https://example.com/history", "OK_HTML", source_type=infer_source_type("historyonly", "https://example.com/history")),
    ]
    tenders.append(TenderCandidate("historyonly", "History Only", "Old Closed Tender", "https://example.com/old", False, "historical archive", "public"))
    finalized = finalize_tender_signals(tenders, logs)

    open_row = next(t for t in finalized if t.tender_title == "Open Tender")
    closed_row = next(t for t in finalized if t.tender_title == "Closed Tender")
    historical_row = next(t for t in finalized if t.tender_title == "Historical Tender")
    blocked_placeholder = next(t for t in finalized if t.source_id == "blocked" and t.found_via == "source_run_log")
    portal_placeholder = next(t for t in finalized if t.source_id == "portal" and t.found_via == "source_run_log")

    assert open_row.retention_target == "bid_now"
    assert closed_row.retention_target == "history"
    assert historical_row.retention_target == "history"
    assert blocked_placeholder.signal_state == "blocked"
    assert portal_placeholder.signal_state == "portal_redirect"

    surrey_log = next(l for l in logs if l.source_id == "surrey")
    blocked_log = next(l for l in logs if l.source_id == "blocked")
    portal_log = next(l for l in logs if l.source_id == "portal")
    paid_log = next(l for l in logs if l.source_id == "paid")
    parsezero_log = next(l for l in logs if l.source_id == "parsezero")
    historyonly_log = next(l for l in logs if l.source_id == "historyonly")
    assert surrey_log.kept_in_bid_now == 1
    assert surrey_log.kept_in_history == 1
    assert surrey_log.final_status == "FETCH_OK_OPEN_FOUND"
    assert blocked_log.final_status == "BLOCKED_FORBIDDEN"
    assert portal_log.final_status == "FETCH_OK_PORTAL_REDIRECT"
    assert paid_log.final_status == "NEEDS_PAID_ACCESS"
    assert parsezero_log.final_status == "FETCH_OK_PARSE_ZERO_ROWS"
    assert historyonly_log.final_status == "FETCH_OK_HISTORICAL_ONLY"

    surrey_detail = TenderCandidate(
        "surrey_bids_public",
        "Surrey public tenders/RFQs/RFPs page",
        "105A Avenue Water Feeder and Distribution Main Improvements",
        "https://www.surrey.ca/business-economy/tenders-rfqs-rfps/105a-avenue-water-feeder-and-distribution-main-improvements",
        True,
        "open",
        "deep_page",
        closing_date="2026-07-09",
        source_url="https://www.surrey.ca/business-economy/tenders-rfqs-rfps",
    )
    fvrd_detail = TenderCandidate(
        "fvrd_tenders",
        "Fraser Valley Regional District - Tenders/RFPs",
        "Hemlock Valley Community Trail Fuel Removal",
        "https://www.fvrd.ca/EN/main/government/tenders-rfps/hemlock-valley-community-trail-fuel-removal.html",
        True,
        "closed",
        "deep_page",
        source_url="https://www.fvrd.ca/EN/main/government/tenders-rfps.html",
    )
    richmond_listing = TenderCandidate(
        "richmond_procurement",
        "Richmond Purchasing public page",
        "Bid Opportunities - City of Richmond, BC",
        "https://www.richmond.ca/business-development/tenders.htm",
        False,
        "unknown",
        "html_listing",
        source_url="https://www.richmond.ca/business-development/tenders.htm",
    )
    assert is_real_opportunity_candidate(surrey_detail) is True
    assert is_real_opportunity_candidate(fvrd_detail) is True
    assert is_real_opportunity_candidate(richmond_listing) is False

    email_open = email_tender_to_candidate(
        EmailTender(
            provider="bidsandtenders.ca",
            source="bidsandtenders.ca",
            issuer="City of Surrey",
            tender_title="Surrey Utility Tie-In",
            civil_relevant=True,
            status="open",
            closing_date="2026-08-01",
            contact_email="procurement@surrey.ca",
            contact_phone="604-555-1212",
            url="https://example.com/surrey-utility",
            found_via="email_alert",
            snippet="synthetic",
            message_id="msg-1",
            received_date="2026-07-02",
            filtered_reason="provider=bidsandtenders.ca",
        )
    )
    email_closed = email_tender_to_candidate(
        EmailTender(
            provider="bidcentral.ca",
            source="BidCentral",
            issuer="City of Kelowna",
            tender_title="Kelowna Office Furniture",
            civil_relevant=False,
            status="closed",
            closing_date="2026-06-01",
            contact_email="",
            contact_phone="",
            url="https://example.com/furniture",
            found_via="email_alert",
            snippet="synthetic",
            message_id="msg-2",
            received_date="2026-07-02",
            filtered_reason="non_civil_email_alert",
        )
    )
    routed = finalize_tender_signals(
        [email_open, email_closed],
        [SourceLog("email_alert_intake", "Email Alert Intake", "folder", "EMAIL_INTAKE_PARSED_ROWS", source_type="email_alert_intake")],
    )
    routed_open = next(t for t in routed if t.tender_title == "Surrey Utility Tie-In")
    routed_closed = next(t for t in routed if t.tender_title == "Kelowna Office Furniture")
    assert routed_open.retention_target == "bid_now"
    assert routed_closed.retention_target == "history"

    print("Tender signal routing tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
