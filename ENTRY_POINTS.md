# Tender Finder Entry Points

## Founder/operator entry point

`Launch_TENDER_FINDER_GUI.bat` is the canonical double-click launcher. It
repairs a missing/broken environment through `setup_tenderfinder_environment.bat`
and then starts `tenderfinder_launcher_gui.py` without leaving a console window.

The GUI exposes Live Run, Offline/Test Run, Self-Test, Keywords, Email Alerts,
Source Checks, results/logs, and advanced settings.

## Shared engine and CLI

- `01 Code\CONNECTOR_SWEEP\tenderfinder_engine.py`: GUI-independent,
  JSON-serializable run/source-test/Self-Test contract.
- `01 Code\CONNECTOR_SWEEP\tenderfinder_demo_three_buckets.py`: workbook
  pipeline called by the engine.
- `01 Code\CONNECTOR_SWEEP\tenderfinder_self_test.py`: command-line wrapper for
  the same authoritative Self-Test used by the GUI and `verify_package.bat`.

Offline CLI example:

```powershell
.\.venv\Scripts\python.exe "01 Code\CONNECTOR_SWEEP\tenderfinder_demo_three_buckets.py" `
  --review-xlsx "inputs\all_live_review.xlsx" `
  --out-dir "C:\tenderfinder_out\cli_offline" `
  --keywords-config "config\keywords.xlsx" `
  --sources-config "config\sources.csv" `
  --run-mode offline --email-intake --no-fetch
```

## Verification and release

- `verify_package.bat`: authoritative offline Self-Test.
- `scripts\offline_ci_check.py`: no-write syntax/import check under network
  denial.
- `scripts\build_clean_release.py`: deterministic allowlist ZIP builder.
- `scripts\verify_clean_release.py`: ZIP path/CRC/hash/extraction verifier.
- `scripts\package_audit.py`: text/workbook secret/private-path audit.

## Mutable locations

Run outputs, history, manifests, settings, backups, email state, and Self-Test
artifacts are beneath `C:\tenderfinder_out` or another explicitly selected
external root. The package-local editable inputs are `config\keywords.xlsx`,
`config\sources.csv`, and the approved review workbook under `inputs\`.

`01 Code\tenderfinder_agent2.py` is frozen legacy code. It is protected by hash
and static isolation checks and is not an operator entry point.
