from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tenderfinder_email_guidance import detect_email_state  # noqa: E402
from tenderfinder_email_intake import (  # noqa: E402
    EmailProviderConfig,
    parse_eml_dir,
    provider_display_name,
    test_email_intake,
)


def main() -> int:
    fixtures = Path(__file__).resolve().parent / "fixtures" / "email_alerts"
    rows = parse_eml_dir(fixtures)
    assert rows, "expected fixture alerts"
    assert all(row.provider in {"bidsandtenders.ca", "bidcentral.ca", "bcbid.gov.bc.ca"} for row in rows)
    assert all(row.snippet.startswith("Email alert parsed.") for row in rows)

    state = detect_email_state("m365_oauth", True, 3, 2)
    assert state.provider_label == "Microsoft 365 / Outlook OAuth"
    assert "connected" in state.label
    assert provider_display_name("imap") == "IMAP fallback"

    result = test_email_intake(fixtures, EmailProviderConfig(provider="manual_folder", connected=True, import_path=str(fixtures)))
    assert result.provider == "Manual local folder import"
    assert result.mailbox_connected is True
    assert result.alert_emails_found >= 6
    assert result.alerts_parsed == 5
    assert result.civil_alerts_found >= 4
    assert result.new_tender_rows_created >= 3
    assert result.recognized_provider_counts["bidsandtenders.ca"] >= 3
    assert result.recognized_provider_counts["bidcentral.ca"] >= 2
    assert result.recognized_provider_counts["bcbid.gov.bc.ca"] >= 1
    assert result.log_path

    print("Provider-neutral email intake tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
