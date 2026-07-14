# RUNBOOK — Tender Finder

All commands run from the package root, in this order the first time:

```bat
setup_venv.bat                 :: 1. one-time environment setup
verify_package.bat             :: 2. recommended: confirm the environment is good
run_demo_synthetic.bat         :: 3. run the offline synthetic demo (section 1 below)
```

See `INSTALL.md` for setup details and `ENTRY_POINTS.md` for a full command
reference. Everything below assumes step 1 (and ideally step 2) already ran.

---

## 1. Offline synthetic demo (no network, safe anywhere)

```bat
run_demo_synthetic.bat
```

Equivalent direct call:

```bat
.venv\Scripts\python.exe "01 Code\CONNECTOR_SWEEP\tenderfinder_demo_three_buckets.py" ^
  --review-xlsx "inputs\all_live_review.xlsx" ^
  --out-dir "demo_out_synthetic" --no-fetch ^
  --email-intake --email-import-path "demo_data\email_alerts"
```

**Expected output** in `demo_out_synthetic\`:

- `TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx` (≈20 sheets:
  Executive_Summary, BID_NOW_Active_Tenders, BID_LATER_Future_Projects,
  Outreach_Tracker, Source_Run_Log, Action_Center, Email_Setup_Guide, …)
- `DEMO_TALKTRACK.md`, `DEMO_BUILD_REPORT.md`, `demo_summary.txt`
- Expected counts with the shipped synthetic data:
  `BID NOW=2 · BID LATER=6 · WATCH=2 · ANALYZED=5`

**Nothing is broken if you then see `Overall: FAIL`.** That line comes from an
optional, separate final-review stage whose job is to catch synthetic/fixture
data before it's presented as production output — on the shipped synthetic
data it is *supposed* to trigger. Specifically two of its sub-checks fail, both
for the same reason (the anti-fixture guard recognizing `SYNTHETIC` markers in
two different places): `No fixture/synthetic/example rows in Outreach_Tracker`
and a dashboard row-count cross-check (`future_full`) that also excludes
fixture-marked rows from its recount. Full explanation in `TEST_RESULTS.md`.
It passes with real, non-synthetic data.

## 2. Fast demo (no live fetch, package inputs)

```bat
run_tenderfinder_demo_fast.bat
```

Uses `inputs\all_live_review.xlsx` (synthetic in this package) and the
`user_data\email_alerts\inbox` folder. Override the review workbook with the
`TENDER_FINDER_REVIEW_XLSX` environment variable.

## 3. Full demo with live public-site sweep (network required)

```bat
run_tenderfinder_demo.bat
```

Performs the Track B live sweep of ~20 public procurement pages, then builds
the workbook. **Not re-verified from this sanitized package** (offline build);
public endpoints may have drifted. Live-run env toggles:
`TENDER_FINDER_DEMO_NO_OPEN=1` (don't auto-open output),
`TENDER_FINDER_DEMO_NO_PAUSE=1` (no pause at end).

## 4. GUI

```bat
Launch_TENDER_FINDER_GUI.bat
```

Tkinter launcher: run demo builds, create/select the email import folder, test
email import, watch progress. Provider-neutral: it never asks for mailbox
credentials — you save/export `.eml` alert files into a folder.

## 5. Email alert intake workflow

1. Register on the public portals (see `Email_Setup_Guide.md` and
   `MANUAL_PORTAL_WORKFLOW.md`).
2. Save incoming alert `.eml` files into `user_data\email_alerts\inbox`
   (or any folder you select in the GUI).
3. GUI → `Test Email Import`, or run any demo with `--email-intake`.
4. Parsed open civil tenders land in **BID NOW**; closed/non-civil rows are
   preserved in history/all-signals sheets with the filter reason.

## 6. Tests

```bat
verify_package.bat                       :: packaged self-check bundle — expected: PASS
```

Full standalone suite (needs `requirements-dev.txt` installed):

```bat
cd "01 Code\CONNECTOR_SWEEP"
for %f in (tests\test_*.py) do @..\..\.venv\Scripts\python.exe "%f"
```

**21 of 23 pass; the other 2 fail for known, harmless reasons explained below —
this is not a broken build.** Re-confirmed 2026-07-04 against a completely
fresh extraction of the distributable ZIP (see `TEST_RESULTS.md` and
`FINAL_HANDOFF_AUDIT.md`). Details:

- `test_launcher_gui.py` — only its end-to-end case fails outside
  `verify_package.bat`, because the e2e demo build hits the anti-fixture guard
  on synthetic data. `verify_package.bat` runs it with
  `TENDER_FINDER_GUI_SKIP_E2E=1` (the packaged, sanctioned mode) → PASS.
- `test_launcher_review_xlsx_consistency.py` — fails identically in the
  original project (launcher/test drift that predates sanitization); kept
  as-is rather than silently "fixed".

`test_workbook_quality.py` auto-detects the packaged synthetic sample and
scales its row-count minimums; validate a real run with
`TENDER_FINDER_DEMO_WORKBOOK=<path>` plus the `TENDER_FINDER_MIN_*_ROWS`
env vars (defaults revert to production values).

The network regression suite (`tests\run_regression.py`) performs live sweeps —
run it only when you intend live fetching.

## 7. Package audit (sanitization re-check)

```bat
.venv\Scripts\python.exe scripts\package_audit.py
```

Rescans every text file and workbook in the package for branding tokens, real
emails, secrets patterns, private paths, and cache folders. Expected:
`PACKAGE AUDIT: PASS`.

## 8. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `ModuleNotFoundError: openpyxl` | venv not created/activated — run `setup_venv.bat` |
| Demo ends with `final-review verification reported FAIL` | Anti-fixture guard on synthetic data — expected, not a bug; see README / TEST_RESULTS.md |
| After running the demo you see a new `__pycache__` folder or `user_data\...\*.json` files | Normal Python/runtime byproducts of actually running the tool on your machine — harmless, safe to delete, and correctly excluded from the distributable ZIP itself |
| `Review workbook not found` | `inputs\all_live_review.xlsx` missing or `TENDER_FINDER_REVIEW_XLSX` points elsewhere |
| Output missing on deep OneDrive path | Auto-redirect writes to `C:\tenderfinder_tmp` — check console note |
| Live sweep returns 0 for BC Bid | Bot-check block — documented `BC_BID_BLOCKED_NO_PUBLIC_FEED` state; use email alerts |
| GUI tests fail headless | Tkinter needs a display; run on a desktop session |

Runtime artifacts you can always delete safely: `__pycache__`,
`user_data\email_alerts\logs\*.json`, `user_data\email_alerts\import_state.json`,
`user_data\tenderfinder_user_config.json`, `demo_out*`, `C:\tenderfinder_out\`.
