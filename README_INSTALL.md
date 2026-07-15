# Tender Finder Installation

## Requirements

- Windows 10/11.
- Python 3.11 or newer available as `py`, `python`, or `python3`.
- Internet access for the first `pip` install and Playwright Chromium setup.

## Install and launch

1. Extract the clean release into a normal local folder. Do not run the program
   itself from iCloud, OneDrive, or another live-sync folder.
2. Double-click `Launch_TENDER_FINDER_GUI.bat`.
3. The launcher detects a missing/broken `.venv`, runs setup, verifies imports,
   and opens the GUI. Setup failures remain visible and return non-zero.
4. Run **Self-Test** and require PASS before the first operational run.

The release ZIP intentionally excludes `.venv`; never copy one from another
computer. Setup does not rewrite the repository-relative launcher. A Desktop
shortcut is optional and points to that stable launcher.

`verify_package.bat` invokes the same strictly offline Self-Test as the GUI.
Runtime outputs/settings are stored beneath `C:\tenderfinder_out`, while
`config\keywords.xlsx` and `config\sources.csv` remain operator-editable files
inside the application folder.
