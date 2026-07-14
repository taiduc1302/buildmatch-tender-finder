# INSTALL — Tender Finder

## Requirements

- **Windows** (primary; macOS launcher scripts are in `packaging\macos\`)
- **Python 3.10+** (validated with 3.13 in the original patch cycle and with
  3.14 during package sanitization — see `PYTHON_VERSION_NOTE.md`)
- No admin rights, no database, no cloud account required.

## Option A — scripted setup (recommended)

```bat
setup_venv.bat
```

This calls `setup_tenderfinder_environment.bat`, which creates a `.venv` in the
package root and installs dependencies. If no Python is found it attempts a
user-local bootstrap via `_python_bootstrap.bat`.

## Option B — manual setup

```bat
python -m venv .venv
.venv\Scripts\pip install -r "01 Code\CONNECTOR_SWEEP\requirements.txt"
```

### Runtime dependencies (`requirements.txt`)

| Package | Used for |
|---|---|
| `openpyxl` | all Excel workbook reading/writing (required) |
| `beautifulsoup4` | HTML parsing in live connectors |
| `playwright` | optional browser-assisted fetch for bot-checked portals (BC Bid); **not needed** for offline/synthetic demo. After install run `playwright install chromium` only if you use this feature. |

### Test/dev dependencies (`requirements-dev.txt`)

Needed only to run the full test suite:

```bat
.venv\Scripts\pip install -r "01 Code\CONNECTOR_SWEEP\requirements-dev.txt"
```

(`pyyaml`, `pandas`, `requests`, `urllib3`, `pdfplumber`, `reportlab` — the last
two only for the Surrey PDF parser test, which generates its own test PDFs.)

## Verify the installation

```bat
verify_package.bat
```

Expected final line: `VERIFY_PACKAGE: PASS`. This step checks your Python
environment and dependencies only — it does not touch the demo yet, so a PASS
here means your install is good, full stop.

Then run the offline demo:

```bat
run_demo_synthetic.bat
```

Expected: `demo_out_synthetic\TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx`
is created — this is the actual product output, and it always succeeds on the
shipped synthetic data.

> You will then see the run end with a **second, unrelated** message:
> `Overall: FAIL` from an optional final-review stage. This is expected and by
> design — it's the anti-fixture guard confirming the synthetic demo data
> would never be mistaken for real production data. It is **not** an install
> problem and does not mean the workbook above wasn't created correctly. See
> `TEST_RESULTS.md` for the exact lines and why each one is safe to ignore on
> synthetic data.

## Notes

- Batch launchers prefer `.venv\Scripts\python.exe` and fall back to `python`
  on PATH.
- Output default locations: package-local folders plus `C:\tenderfinder_out\`
  for some launcher-driven runs (created automatically; safe to delete).
- Long-path/OneDrive issues: the workbook writer automatically falls back to a
  short local temp path if the target path is too long (see
  `tenderfinder_live_link_checker.py` notes).
