# TENDER_FINDER Install

## Requirements

- Windows with Python 3.10 or newer
- Internet access for `pip install` and Playwright browser setup

## Setup

1. Unzip the TENDER_FINDER runtime package anywhere.
2. Run `setup_venv.bat`.
3. Wait for the local `.venv` creation, `pip install`, and Playwright Chromium install to finish.
4. Run `verify_package.bat`.
5. Launch TENDER_FINDER from `Launch_TENDER_FINDER_GUI.bat` or use the batch launchers.

## Notes

- The package is self-contained and should not require `C:\t\TENDER_FINDER_Patch_5_0` or any developer-only path.
- The default review workbook is loaded from `inputs\all_live_review.xlsx` when present.
- Manual Email Alert Import is provider-neutral in this patch. Gmail OAuth, Microsoft OAuth, and IMAP are intentionally not implemented here.
