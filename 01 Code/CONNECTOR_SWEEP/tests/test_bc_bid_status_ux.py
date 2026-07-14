from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tenderfinder_demo_three_buckets import (  # noqa: E402
    DemoData,
    SourceLog,
    bc_bid_status_note,
    write_demo_summary,
)
from tenderfinder_email_guidance import detect_email_state  # noqa: E402

# Patch 5.17 Track 2: prove the BC-Bid-blocked case is distinguished from a
# genuine zero-result, using a SIMULATED blocked status (not a real hit
# against bcbid.gov.bc.ca - the invariant for this patch is explicit that
# repeated live BC Bid hits should be avoided beyond what's strictly
# required).


def test_bc_bid_status_note_blocked() -> None:
    note = bc_bid_status_note("BC_BID_BLOCKED_NO_PUBLIC_FEED")
    assert note, "expected a non-empty clarifying note for the blocked status"
    assert "bot-check" in note
    assert "not a TENDER_FINDER problem" in note
    assert "docs/BC_BID_NETWORK_AUDIT.md" in note


def test_bc_bid_status_note_ok_unchanged() -> None:
    assert bc_bid_status_note("OK_BROWSER_COOKIE_REPLAY") == ""
    assert bc_bid_status_note("NOT_ATTEMPTED") == ""


def test_bc_bid_status_note_user_action_required() -> None:
    """Patch 5.18 Task C: the new status from the headed user-assisted
    browser fallback (Task A) must get its own distinct message - not the
    generic "temporarily blocked" text - and must never read like a
    genuine zero-result."""
    note = bc_bid_status_note("BC_BID_BLOCKED_BROWSER_CHECK_USER_ACTION_REQUIRED")
    assert note, "expected a non-empty clarifying note for the user-action-required status"
    assert "person" in note.lower() or "clear" in note.lower()
    assert "does not log in" in note or "not log in" in note.lower()
    assert "CAPTCHA" in note
    # Must be distinct wording from the generic blocked-status note, not a
    # reuse of the same text.
    assert note != bc_bid_status_note("BC_BID_BLOCKED_NO_PUBLIC_FEED")


def test_bc_bid_status_note_user_check_not_completed() -> None:
    """Product Task D: when the user never completed the browser check
    within the (now 5-minute) window, the status is its own honest state -
    never a generic block, never a fake zero."""
    note = bc_bid_status_note("BC_BID_USER_CHECK_NOT_COMPLETED")
    assert note, "expected a non-empty note for the not-completed status"
    assert "not completed" in note.lower() or "was not completed" in note.lower()
    assert "NOT a genuine zero-result" in note
    assert "never logs in" in note
    assert note != bc_bid_status_note("BC_BID_BLOCKED_NO_PUBLIC_FEED")
    assert note != bc_bid_status_note("BC_BID_BLOCKED_BROWSER_CHECK_USER_ACTION_REQUIRED")


def test_write_demo_summary_surfaces_user_check_not_completed() -> None:
    data = DemoData()
    logs = [SourceLog(
        "bc_bid_public", "BC Bid public open opportunities", "https://bcbid.gov.bc.ca",
        "BC_BID_USER_CHECK_NOT_COMPLETED",
    )]
    email_state = detect_email_state(False, 0, 0)
    with tempfile.TemporaryDirectory() as tmp:
        summary_path = Path(tmp) / "demo_summary.txt"
        write_demo_summary(summary_path, data, [], logs, 1.0, 2.0, Path(tmp) / "wb.xlsx", email_state)
        text = summary_path.read_text(encoding="utf-8")
    assert "BC Bid status: BC_BID_USER_CHECK_NOT_COMPLETED" in text
    assert "NOT a genuine zero-result" in text


def test_email_guidance_uses_live_bid_later_count_not_stale_5393() -> None:
    """Product Task G: the email-setup text carried a hardcoded '5,393
    future-project leads' for several patches after the corrected Track A
    count became 7,537. The count must now come from the live run."""
    from tenderfinder_email_guidance import format_email_setup_status
    state = detect_email_state(False, 0, 0)
    text = format_email_setup_status(state, bid_later_count=7537)
    assert "7,537 future-project leads" in text
    assert "5,393" not in text
    # Without a count, no number is claimed at all - never a stale one.
    text_no_count = format_email_setup_status(state)
    assert "5,393" not in text_no_count
    assert "future-project leads" in text_no_count


def test_write_demo_summary_surfaces_blocked_status() -> None:
    data = DemoData()
    logs = [SourceLog("bc_bid_public", "BC Bid public open opportunities", "https://bcbid.gov.bc.ca", "BC_BID_BLOCKED_NO_PUBLIC_FEED")]
    email_state = detect_email_state(False, 0, 0)
    with tempfile.TemporaryDirectory() as tmp:
        summary_path = Path(tmp) / "demo_summary.txt"
        write_demo_summary(summary_path, data, [], logs, 1.0, 2.0, Path(tmp) / "wb.xlsx", email_state)
        text = summary_path.read_text(encoding="utf-8")
    assert "BC Bid status: BC_BID_BLOCKED_NO_PUBLIC_FEED" in text
    assert "temporarily blocked by the site's bot-check" in text


def test_write_demo_summary_ok_status_unchanged() -> None:
    data = DemoData()
    logs = [SourceLog("bc_bid_public", "BC Bid public open opportunities", "https://bcbid.gov.bc.ca", "OK_BROWSER_COOKIE_REPLAY")]
    email_state = detect_email_state(False, 0, 0)
    with tempfile.TemporaryDirectory() as tmp:
        summary_path = Path(tmp) / "demo_summary.txt"
        write_demo_summary(summary_path, data, [], logs, 1.0, 2.0, Path(tmp) / "wb.xlsx", email_state)
        text = summary_path.read_text(encoding="utf-8")
    assert "BC Bid status: OK_BROWSER_COOKIE_REPLAY" in text
    assert "temporarily blocked" not in text
    # The status line must be followed directly by the Email intake status
    # line (Patch 5.22), not an inserted blank BC Bid explanation line, when
    # nothing needs explaining.
    lines = text.splitlines()
    status_idx = next(i for i, l in enumerate(lines) if l.startswith("BC Bid status:"))
    assert lines[status_idx + 1].startswith("Email intake status:")
    # Likewise, no BC Bid explanatory note should be inserted immediately
    # before the BID NOW total line when nothing needs explaining.
    bid_now_idx = next(i for i, l in enumerate(lines) if l.startswith("BID NOW total:"))
    assert lines[bid_now_idx - 1].startswith("Email rejected/duplicate files:")


def test_write_demo_summary_surfaces_user_action_required() -> None:
    """Patch 5.18 Task A/C: when the headed user-assisted fallback still
    could not get past BC Bid's browser-check, demo_summary.txt must say
    so plainly - never falling back to a bare "BC Bid open civil: 0" that
    would be indistinguishable from BC Bid genuinely finding nothing."""
    data = DemoData()
    logs = [SourceLog(
        "bc_bid_public", "BC Bid public open opportunities", "https://bcbid.gov.bc.ca",
        "BC_BID_BLOCKED_BROWSER_CHECK_USER_ACTION_REQUIRED",
    )]
    email_state = detect_email_state(False, 0, 0)
    with tempfile.TemporaryDirectory() as tmp:
        summary_path = Path(tmp) / "demo_summary.txt"
        write_demo_summary(summary_path, data, [], logs, 1.0, 2.0, Path(tmp) / "wb.xlsx", email_state)
        text = summary_path.read_text(encoding="utf-8")
    assert "BC Bid status: BC_BID_BLOCKED_BROWSER_CHECK_USER_ACTION_REQUIRED" in text
    assert "BC Bid open civil: 0" in text, "the raw count line should still be present"
    # ...but it must not be the ONLY signal - the clarifying note must also
    # be there, distinguishing this from a genuine zero-result.
    assert "needs a person to clear" in text
    assert "temporarily blocked by the site's bot-check" not in text, "must use the distinct user-action message, not the generic one"


def main() -> int:
    tests = [
        test_bc_bid_status_note_blocked,
        test_bc_bid_status_note_ok_unchanged,
        test_bc_bid_status_note_user_action_required,
        test_bc_bid_status_note_user_check_not_completed,
        test_write_demo_summary_surfaces_user_check_not_completed,
        test_email_guidance_uses_live_bid_later_count_not_stale_5393,
        test_write_demo_summary_surfaces_blocked_status,
        test_write_demo_summary_ok_status_unchanged,
        test_write_demo_summary_surfaces_user_action_required,
    ]
    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")
    print("BC Bid status UX test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
