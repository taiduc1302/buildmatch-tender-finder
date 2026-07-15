# Install Tender Finder on Windows

Tender Finder is a clickable Python application, not a self-contained EXE.

## Requirements

- Windows 10/11.
- Python 3.11+ available through `py`, `python`, or `python3`.
- Internet access for first-run packages and Playwright Chromium.
- No admin rights, database, cloud account, or portal credentials are required.

## Recommended setup

Extract the clean ZIP into a normal local folder and double-click:

```text
Launch_TENDER_FINDER_GUI.bat
```

The launcher checks `.venv`, calls `setup_tenderfinder_environment.bat` when
needed, verifies imports, and opens the GUI. If Python is unavailable, the
bootstrap prints an official download instruction. Dependency or Chromium
install failures remain visible and return non-zero.

The ZIP deliberately excludes `.venv`; do not copy one from another computer.
Setup never rewrites the canonical repository-relative launcher. An optional
Desktop shortcut points to that launcher.

## Manual setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
```

## Verify

Double-click `verify_package.bat` or run:

```powershell
.\.venv\Scripts\python.exe "01 Code\CONNECTOR_SWEEP\tenderfinder_self_test.py" --root .
```

Require `SELF_TEST: PASS`. Self-Test is strictly offline and writes artifacts
beneath `C:\tenderfinder_out`, not the program folder.
