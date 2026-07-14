# LINK_PREFLIGHT_INTEGRATION_CHANGELOG.md

## Patch Attempt 4 — Link Preflight Integrated HOTFIX

Package base:

- `TENDER_FINDER_bulk_harvest_patch_attempt_3.zip`

Integrated package:

- `TENDER_FINDER_Link_Checker_v2.1.0.zip`

Final package target:

- `TENDER_FINDER_bulk_harvest_patch_attempt_4_link_preflight_integrated_HOTFIX.zip`

---

## 1. Purpose

Patch Attempt 4 integrates the accepted live link checker into the real Tender Finder / bulk harvester codebase as a preflight/source-health gate.

This patch does not rebuild the project, recreate the master workbook, replace the harvester, or overwrite the protected v6 workbook.

---

## 2. Files added

Added into:

```text
0623 v4 Tender Finder Final / 01 Code / CONNECTOR_SWEEP /
```

- `tenderfinder_live_link_checker.py`
- `tenderfinder_link_preflight.py`
- `tests/run_failure_tests.py`
- `tests/LAST_TEST_RUN.txt`
- `tests/fixtures/test_register.csv`
- `LINK_PREFLIGHT_INTEGRATION_CHANGELOG.md`
- `LINK_PREFLIGHT_FINAL_TEST_REPORT.md`
- `PATCH4_FILE_INVENTORY_DIFF.md`

---

## 3. Files modified

Modified existing files only where needed:

- `tenderfinder_raw_sweep.py`
  - Added preflight CLI options.
  - Wired `--preflight-links` into the main runner.
  - Added preflight-only execution path.
  - Added source-health gate hook before connector runs.
  - Preserved existing list, dry-run, bulk-intake, and write safety behavior.

- `tenderfinder_live_link_checker.py`
  - Copied from accepted v2.1.0 package.
  - Added support for the real master workbook URL column alias: `URL / Portal`.
  - Added these URL aliases through normalization:
    - `URL / Portal`
    - `URL`
    - `Portal`
    - `URL/Portal`
    - `official_url`
    - `primary_url`
    - `example_url`
    - `secondary_urls`
    - `example_relevant_page_or_record_url`

- `RUN_ALL_SOURCES_SAFE.md`
  - Added Patch 4 preflight command, outputs, and routing/safety rules.

---

## 4. New CLI options in `tenderfinder_raw_sweep.py`

- `--preflight-links`
- `--preflight-output-dir`
- `--preflight-no-search`
- `--preflight-search-provider`
- `--preflight-timeout`
- `--preflight-retries`
- `--preflight-workers`
- `--preflight-rate-limit`
- `--preflight-fail-on-broken`
- `--include-broken-sources`

`python tenderfinder_raw_sweep.py --help` shows these options.

---

## 5. Safety behavior preserved

The integration does not write to the master workbook during preflight.

The protected workbook remains protected:

```text
00 Master / TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx
```

Preflight output preserves original URLs and does not delete or overwrite Source Register rows.

Broken URL statuses are excluded from simple scraping unless `--include-broken-sources` is provided:

- `BROKEN_DNS`
- `BROKEN_SSL`
- `BROKEN_404`
- `BROKEN_OTHER`
- `FIX_URL_FIRST`
- `NO_REPLACEMENT_FOUND`

The following are routed to review/connector/manual/retry workflows and are not treated as deleted rows:

- `FORBIDDEN_BUT_LIKELY_VALID`
- `NEEDS_CONNECTOR_NOT_SIMPLE_SCRAPE`
- `LOGIN_OR_MANUAL`
- `TIMEOUT_RETRY_NEEDED`

---

## 6. Known limitation

The sandbox environment used for this patch had DNS/network resolution failures. Live HTTP tests against public URLs produced false DNS failures or could not complete within the sandbox timeout. Integrated dry-run preflight successfully proved that the command runs through `tenderfinder_raw_sweep.py`, reads the real master workbook, recognizes `URL / Portal`, and writes the required output files.

A full live preflight should be rerun from a normal TENDER_FINDER office/residential network before treating the link-health results as business-valid.
