# ENTRY POINTS — Tender Finder

Every command you can run in this package, what it does, and where its output
lands. All paths are relative to the package root; all commands assume
`setup_venv.bat` has been run once (see `INSTALL.md`).

## Main demo command (start here)

| Command | What it does | Output |
|---|---|---|
| `run_demo_synthetic.bat` | **Offline, synthetic, no network/credentials.** Builds the three-bucket workbook from the shipped synthetic review workbook + synthetic emails. | `demo_out_synthetic\TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx` + `DEMO_TALKTRACK.md`, `DEMO_BUILD_REPORT.md`, `demo_summary.txt` in the same folder |

## Main Python script (what the batch files call)

| Script | Role |
|---|---|
| `01 Code\CONNECTOR_SWEEP\tenderfinder_demo_three_buckets.py` | The engine. CLI: `--review-xlsx <path> --out-dir <path> [--no-fetch] [--email-intake] [--email-import-path <folder>]`. Reads the review workbook, optionally sweeps live public tender pages, runs email alert intake, scores/routes rows into BID NOW / BID LATER / WATCH buckets, writes the workbook + reports, then (if a master template is present) builds a slim "user master" workbook guarded by the anti-fixture check. |

## Other run commands

| Command | What it does | Output |
|---|---|---|
| `run_tenderfinder_demo_fast.bat` | Same engine, `--no-fetch`, using `inputs\all_live_review.xlsx` (synthetic here) + `user_data\email_alerts\inbox` | `C:\tenderfinder_out\demo_p523_fast\` (created automatically) |
| `run_tenderfinder_demo.bat` | Full run **with** live public-site fetching (network required; not re-tested from this package — see `DEMO_LIMITATIONS.md`) | `C:\tenderfinder_out\demo_p523\` |
| `Launch_TENDER_FINDER_GUI.bat` | Tkinter GUI: run demos, manage the email import folder, watch progress | Same output locations as the demo it triggers |
| `01_SETUP_AND_RUN_LIVE.bat` | Convenience: setup + full live run in one step | Same as `run_tenderfinder_demo.bat` |
| `02_RUN_FAST_TEST_NO_FETCH.bat` | Convenience: setup + fast offline run in one step | Same as `run_tenderfinder_demo_fast.bat` |

## Audit command

| Command | What it does | Output |
|---|---|---|
| `.venv\Scripts\python.exe scripts\package_audit.py` | Re-scans every text file and Excel workbook (cell text included) in the package for brand tokens, real emails, secrets, private paths, and cache folders | Prints `PACKAGE AUDIT: PASS` or lists findings to the console; no file output |

## Verification command

| Command | What it does | Output |
|---|---|---|
| `verify_package.bat` | Runs the packaged self-check bundle: empty-inbox email test, synthetic `.eml` fixture parser tests, folder UX/routing tests, GUI logic tests (with the sanctioned `SKIP_E2E` flag) | Prints `VERIFY_PACKAGE: PASS`/`FAIL` to the console; no file output |

## Workbook generation (direct call, for scripting/automation)

```bat
.venv\Scripts\python.exe "01 Code\CONNECTOR_SWEEP\tenderfinder_demo_three_buckets.py" ^
  --review-xlsx "inputs\all_live_review.xlsx" ^
  --out-dir "my_output_folder" ^
  --no-fetch ^
  --email-intake --email-import-path "demo_data\email_alerts"
```

Swap `--review-xlsx` for your own workbook and drop `--no-fetch` to enable
live sweeping (network required, not re-verified from this package).

## Where outputs are created

| Location | What's there |
|---|---|
| `<--out-dir>\` (e.g. `demo_out_synthetic\`) | The three-bucket demo workbook + build reports for that run |
| `C:\tenderfinder_out\` | Default output root used by some launcher-driven flows (auto-created; safe to delete) |
| `C:\tenderfinder_out\final_user_master_<timestamp>\` | The slim "user master" workbook + a copy of the full demo workbook, from the optional final-review stage |
| `user_data\email_alerts\inbox\` | Where you drop `.eml` alert files for import (starts empty) |
| `user_data\email_alerts\logs\` | Import test logs (safe to delete) |

## Test entry points

| Command | What it does |
|---|---|
| `01 Code\CONNECTOR_SWEEP\tests\test_*.py` (run individually with the venv's python) | 23 standalone test scripts — see `TEST_RESULTS.md` for current pass/fail status and why |
| `01 Code\CONNECTOR_SWEEP\tests\run_regression.py --all --output-dir <path>` | Full network regression suite (live sweeps) — only run this when you intend live fetching |
