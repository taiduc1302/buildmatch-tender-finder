from __future__ import annotations

from dataclasses import dataclass

from tenderfinder_email_intake import CANONICAL_ALERT_SENDERS, is_alert_sender


@dataclass
class EmailSetupState:
    state: str
    provider: str = "manual_folder"
    canonical_count: int = 0
    tender_candidate_count: int = 0
    mailbox_connected: bool = False
    is_fixture_source: bool = False

    @property
    def label(self) -> str:
        if self.state == "STATE_A":
            if self.is_fixture_source:
                return (
                    f"FIXTURE/SYNTHETIC TEST DATA - {self.provider_label} connected; {self.canonical_count} "
                    "canonical-domain alert emails detected from checked-in test fixtures, NOT a live alert "
                    "feed; parsed tender rows depend on alert content."
                )
            return (
                f"LIVE - {self.provider_label} connected; {self.canonical_count} canonical-domain alert emails "
                "detected; parsed tender rows depend on alert content."
            )
        if self.state == "STATE_B":
            return f"READY - {self.provider_label} connected but 0 alert emails found yet."
        return "INTAKE OFF - no email alert provider is connected in this run."

    @property
    def provider_label(self) -> str:
        return {
            "gmail_oauth": "Gmail OAuth",
            "m365_oauth": "Microsoft 365 / Outlook OAuth",
            "imap": "IMAP fallback",
            "manual_folder": "Manual local folder import",
        }.get(self.provider, self.provider or "Email Alert Intake")


def detect_email_state(
    provider_or_connected: str | bool,
    mailbox_connected_or_count: bool | int,
    canonical_count: int,
    tender_candidate_count: int = 0,
    is_fixture_source: bool = False,
) -> EmailSetupState:
    if isinstance(provider_or_connected, bool):
        provider = "gmail_oauth" if provider_or_connected else "manual_folder"
        mailbox_connected = bool(provider_or_connected)
        canonical = int(mailbox_connected_or_count)
    else:
        provider = provider_or_connected or "manual_folder"
        mailbox_connected = bool(mailbox_connected_or_count)
        canonical = canonical_count
    if not mailbox_connected:
        return EmailSetupState("STATE_C", provider, canonical, tender_candidate_count, False, is_fixture_source)
    if canonical > 0:
        return EmailSetupState("STATE_A", provider, canonical, tender_candidate_count, True, is_fixture_source)
    return EmailSetupState("STATE_B", provider, 0, tender_candidate_count, True, is_fixture_source)


def email_setup_rows(state: EmailSetupState) -> list[list[str]]:
    status = state.label
    return [
        ["1", "TENDER_FINDER Launcher", "Click Create / Open Email Import Folder. TENDER_FINDER creates the package-local inbox automatically and opens it for you.", "This removes guesswork about where .eml files should go in the runtime package.", "Local package folder", status],
        ["2", "Approved alert emails", "Save or copy approved .eml alert files into the opened inbox folder. Or click Select Existing Email Folder to use a OneDrive/local folder instead.", "Manual import is provider-neutral and does not require mailbox passwords or OAuth in this patch.", "Local or OneDrive folder", status],
        ["3", "TENDER_FINDER Launcher", "Click Test Email Import. This is dry-run only: it parses, counts, and logs results without moving or deleting your .eml files.", "You can confirm provider recognition, rejected reasons, duplicates, and civil/open rows before the demo run.", "Local package folder", status],
        ["4", "TENDER_FINDER Launcher", "Click Run With Email Alerts after the dry-run looks right.", "Open/actionable rows feed BID NOW; non-actionable rows stay in Tender_Signals_All with an honest filtered_reason.", "Local package folder", status],
        ["5", "bidsandtenders.ca", "Register as a vendor, follow Surrey, Maple Ridge, Township of Langley, City of Langley, Richmond, Pitt Meadows, and Fraser Health; enable civil email alerts. Verify exact category labels on the portal.", "Most Lower Mainland municipal live tenders sit behind this free vendor login; TENDER_FINDER reads alert emails instead of logging in.", "https://www.bidsandtenders.ca", status],
        ["6", "BC Bid", "Use public browse where possible; register as a supplier only to submit or enable notifications. Select civil/site-prep/water/sewer/road categories where available; verify exact labels on the portal.", "Provincial and public-body opportunities can arrive as no-login browse results or supplier notifications.", "https://www.bcbid.gov.bc.ca", status],
        ["7", "BidCentral", "Confirm membership tier and enable civil/construction alerts if included.", "Construction bid network alerts can feed BID NOW without portal scraping.", "https://www.bidcentral.ca", status],
        ["8", "CivicInfo BC", "Monitor or subscribe to local-government bids if available.", "Useful backup aggregator for municipal opportunities.", "https://www.civicinfo.bc.ca/bids", status],
    ]


def format_email_setup_status(state: EmailSetupState, bid_later_count: int | None = None) -> str:
    # The BID LATER count must come from the live run, never a hardcoded
    # snapshot: a stale "5,393" was shown to users for several patches after
    # the corrected Track A count became 7,537.
    if bid_later_count:
        bid_later_line = f"BID LATER still works fully with {bid_later_count:,} future-project leads."
    else:
        bid_later_line = "BID LATER still works fully with the future-project leads in this workbook."
    return f"""
----------------------------------------------------------------------------
TENDER_FINDER LIVE-TENDER EMAIL SETUP - status: {state.state}
----------------------------------------------------------------------------
WHY THIS MATTERS:
  Cities like Surrey, Maple Ridge, Township Langley, Richmond, and Pitt
  Meadows publish their live biddable tenders on portal systems. TENDER_FINDER does
  not log in or store passwords. Instead, you connect an approved email
  intake provider, enable civil alert emails, and TENDER_FINDER reads those alerts
  from your own inbox or imported local folder.

WHERE TO REGISTER:
  1. bidsandtenders.ca - vendor registration, civil/roads/utilities/site
     servicing alerts. Verify exact category labels on the portal.
     URL: https://www.bidsandtenders.ca
  2. bcbid.gov.bc.ca - supplier registration for notifications/submission.
     Public browse requires no login, but automation may hit browser-check.
     URL: https://www.bcbid.gov.bc.ca
  3. bidcentral.ca - confirm membership tier and construction/civil alerts.
     URL: https://www.bidcentral.ca
  4. civicinfo.bc.ca/bids - optional local-government bids aggregator.
     URL: https://www.civicinfo.bc.ca/bids

WHAT HAPPENS IF YOU DO THIS:
  Alert emails start arriving in your inbox. In this patch, open TENDER_FINDER Launcher,
  click Create / Open Email Import Folder, save or copy approved .eml alerts
  into that folder, click Test Email Import, then click Run With Email
  Alerts. TENDER_FINDER can fill BID NOW with real open tenders, closing dates,
  contacts, and links.

WHAT HAPPENS IF YOU DO NOT DO THIS:
  BID NOW stays limited to public-page signals and historically closed tenders.
  {bid_later_line}

YOUR CURRENT STATUS:
  {state.label}
  Active provider: {state.provider_label}
  Manual import only in this patch: Gmail OAuth, Microsoft OAuth, and IMAP are
  intentionally not implemented here.
----------------------------------------------------------------------------
""".strip()


def print_email_setup_status(state: EmailSetupState, bid_later_count: int | None = None) -> None:
    print(format_email_setup_status(state, bid_later_count))
