# TENDER_FINDER Install

## Requirements

- Windows 10/11 with Python 3.10 or newer available as `py` or `python`
- Internet access for `pip install` and Playwright browser setup

## Setup

1. Unzip or clone TENDER_FINDER into a normal local folder. Avoid iCloud,
   OneDrive, or another live-sync folder for the program itself.
2. Double-click `Launch_TENDER_FINDER_GUI.bat`. It automatically runs the
   one-time setup when `.venv` is missing, then opens the GUI.
3. In the GUI, click **Run Self-Test** and require `PASS` before the first
   operational run.

Optional command-line verification: double-click `verify_package.bat`. It
uses the same shared, strictly offline Self-Test implementation as the GUI.

## Notes

- The package is self-contained and does not require a developer-only path.
- The default review workbook is loaded from `inputs\all_live_review.xlsx` when present.
- Runtime outputs and saved settings go to `C:\tenderfinder_out`, not into the
  program folder. This keeps runs isolated and avoids sync conflicts.
- If an older package-local email inbox contains `.eml` files, TENDER_FINDER
  continues to discover that folder read-only; it never moves or deletes the
  messages. New settings and logs still go to the external runtime root.
- `config\keywords.xlsx` and `config\sources.csv` are intentional operator-
  editable configuration files. Keep normal backups of them.
- Manual Email Alert Import is provider-neutral in this patch. Gmail OAuth, Microsoft OAuth, and IMAP are intentionally not implemented here.
