# Tender Finder Weekly Runbook

## 1. Open and preflight

1. Double-click `Launch_TENDER_FINDER_GUI.bat`.
2. In **Keywords**, click **Validate Keywords**.
3. Click **Run Self-Test**.
4. Require PASS, zero failed, and zero no-fixture checks. Review any explicit
   skips/exclusions in the manifest rather than treating them as passes.

## 2. Safe offline run

Click **Offline/Test Run**. This rebuilds from packaged/local inputs with
`--no-fetch` and makes no site requests. Confirm output/manifest paths are
outside the program folder and inspect `Keyword_Change_Audit`.

Direct equivalent:

```powershell
.\.venv\Scripts\python.exe "01 Code\CONNECTOR_SWEEP\tenderfinder_demo_three_buckets.py" `
  --review-xlsx "inputs\all_live_review.xlsx" `
  --out-dir "C:\tenderfinder_out\weekly_offline" `
  --email-intake --no-fetch --run-mode offline
```

## 3. Optional live run

Use **Live Run** only when public network access is intended. The source
registry, not a second hardcoded list, governs source selection. Do not run all
sources merely to test one; select and use **Live Source Test** for a controlled
single-source check.

Tender Finder uses public no-login endpoints, conservative timeouts, TLS
verification, public-address validation, and redirect revalidation. It does not
bypass browser checks or CAPTCHA. Read each source's structured status rather
than interpreting zero rows as success.

## 4. Weekly review

- Review score/tier/bucket changes in `Keyword_Change_Audit`.
- Work the slim user master.
- Update `Assigned To`, `Status`, `Notes`, and Weekly Review Log normally;
  stable IDs preserve them on the next run.
- If a record moved below a gate, find it in the audit/preserved moved-record
  path; it must not silently disappear.

## 5. Source maintenance

- **Validate Configuration**: schema/adapter/URL only, no parser/network.
- **Offline Parser Test**: real parser with sanitized local fixture.
- **Live Source Test**: explicit selected source, network used, structured
  counts; only this action can assign `verified_live`.

New entries start disabled. Keep unsupported sites as disabled drafts until a
code adapter and fixture exist.

## 6. Keyword maintenance

Edit `config\keywords.xlsx`, save, Validate, Reload, and run offline first.
Current rules always govern current replayable scoring (`RESCORE_ALWAYS`). A
verified external LKG snapshot is emergency continuity only and is visibly
identified when used; repair the canonical workbook promptly.

## 7. Troubleshooting

- Missing Python: install Python 3.11+ from python.org and enable PATH.
- Setup failure: read the visible non-zero setup error; rerun the launcher.
- Self-Test FAIL: inspect the manifest/output path shown in the GUI.
- BC Bid unavailable: complete a visible browser check yourself if offered, or
  accept the honest source-level failure; other sources can continue.
- Missing review workbook: browse to an approved workbook; the saved setting is
  external under `C:\tenderfinder_out\state\user\settings`.

Do not delete the editable canonical config. Runtime folders under
`C:\tenderfinder_out` can be archived according to normal data-retention rules.
