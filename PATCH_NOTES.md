# Patch Notes - 5.23

## Scope

This patch is limited to launcher GUI UX cleanup, auto-open/output consistency, and truthful manual Email Alert Import evidence.

## What Changed

- Added package-root detection for portable runtime installs.
- Added package-local `user_data/email_alerts/inbox`, `processed`, `rejected`, and `logs` folders with placeholder `README.md` files.
- Added package-local user config at `user_data/tenderfinder_user_config.json`.
- Added duplicate-state tracking at `user_data/email_alerts/import_state.json`.
- Expanded `.eml` parsing for multipart, HTML, base64, quoted-printable, utf-8, iso-8859-1, table text, anchor links, and SendGrid-style redirect links.
- Reworked the launcher into a tabbed layout sized for 1366x768 with clearer Run, Email Alerts, Source Checks, Results / Logs, and Settings / Advanced sections.
- Added launcher actions for creating/opening the email import folder, selecting an existing folder, dry-run testing, reset/open helpers, and direct post-run open buttons for workbook, output folder, report, and summary.
- Added optional auto-open workbook behavior after successful builds, while preserving `TENDER_FINDER_DEMO_NO_OPEN=1` for unattended verification.
- Corrected patch-version labeling to 5.23 in the builder output and launch scripts.
- Corrected email-intake summary/report counting so source-log placeholder rows are not misreported as parsed tender rows.
- Added clearer email-intake evidence labels to the demo report and summary outputs, including tracking-link provenance and cleaned alert titles.

## Explicitly Not In Scope

- Gmail OAuth
- Microsoft OAuth
- IMAP mailbox access
- Changes to BID LATER scoring
- Changes to municipal tender-source fetch logic beyond email-alert routing
