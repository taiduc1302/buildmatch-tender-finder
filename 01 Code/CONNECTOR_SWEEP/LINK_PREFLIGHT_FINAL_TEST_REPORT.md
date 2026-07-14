# LINK_PREFLIGHT_FINAL_TEST_REPORT.md

## 1. Scope

Patch Attempt 4 integrates `TENDER_FINDER_Link_Checker_v2.1.0` into the real Patch Attempt 3 bulk harvester package.

Base package used:

```text
TENDER_FINDER_bulk_harvest_patch_attempt_3.zip
```

Integrated checker package:

```text
TENDER_FINDER_Link_Checker_v2.1.0.zip
```

Final package:

```text
TENDER_FINDER_bulk_harvest_patch_attempt_4_link_preflight_integrated_HOTFIX.zip
```

---

## 2. Commands run and results

All commands were run from:

```text
0623 v4 Tender Finder Final / 01 Code / CONNECTOR_SWEEP /
```

### Compile checks

```bash
python -m py_compile tenderfinder_raw_sweep.py
python -m py_compile tenderfinder_guards.py
python -m py_compile tenderfinder_master_io.py
python -m py_compile tenderfinder_source_registry.py
python -m py_compile tenderfinder_bulk_io.py
python -m py_compile tenderfinder_live_link_checker.py
python -m py_compile tenderfinder_link_preflight.py
```

Result: PASS. All files compiled successfully.

### Help checks

```bash
python tenderfinder_raw_sweep.py --help
python tenderfinder_live_link_checker.py --help
```

Result: PASS.

Confirmed: `python tenderfinder_raw_sweep.py --help` visibly exposes these new options:

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

### Existing list command

```bash
python tenderfinder_raw_sweep.py --list
```

Result: PASS. Existing command still works and lists 16 connectors.

### V6 write refusal check

```bash
python tenderfinder_raw_sweep.py --only twp_langley_devactivity --max-records 1 --write-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx"
```

Result: PASS. The runner refused the protected v6 workbook before pull, backup, or write.

Observed message:

```text
ERROR: Refusing to write to protected v6 master workbook
```

### Failure-case tests

```bash
python tests/run_failure_tests.py
```

Result: PARTIAL / ENVIRONMENT-BLOCKED.

Observed result in sandbox:

```text
20 passed, 4 failed
```

Failed fixture checks were caused by sandbox DNS/network resolution failures. Public known-good URLs such as GitHub and BC Hydro resolved as `BROKEN_DNS` in the sandbox. The failure-case harness itself ran and confirmed input-error handling, dry-run behavior, preflight-fail-on-broken behavior, output generation, Fix Queue behavior, and diagnostic columns.

Failed cases:

- `TST-01 -> BROKEN_DNS`, expected `OK` or `OK_REDIRECTED`
- `TST-04 -> BROKEN_DNS`, expected `BROKEN_404`
- `TST-08 -> BROKEN_DNS`, expected `OK`, `OK_REDIRECTED`, or `FORBIDDEN_BUT_LIKELY_VALID`
- `TST-01 safe_to_scrape=YES`, observed `NO` because the URL was classified as DNS-broken in sandbox

Action: rerun `python tests/run_failure_tests.py` from a normal TENDER_FINDER office/residential network before relying on live HTTP classification results.

### Integrated preflight through `tenderfinder_raw_sweep.py`

Attempted live command:

```bash
python tenderfinder_raw_sweep.py \
  --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx" \
  --preflight-links \
  --preflight-no-search \
  --preflight-output-dir "./link_audit_out" \
  --preflight-timeout 20 \
  --preflight-retries 2 \
  --preflight-workers 6
```

Result: ENVIRONMENT-BLOCKED / DID NOT COMPLETE IN SANDBOX.

The command did run through `tenderfinder_raw_sweep.py` and successfully read the real master workbook sheet `Source_Register`. It recognized the real URL column alias `URL / Portal` as `official_url`. The run then stalled on live HTTP checks because the sandbox could not reliably resolve public DNS and did not complete before the execution timeout.

Observed evidence before timeout:

- Input workbook opened for read only.
- Sheet selected: `Source_Register`.
- Source rows loaded: 68.
- Extractable URLs: 68.
- Replacement search disabled by `--preflight-no-search`.
- Processing started through integrated wrapper.

### Integrated preflight dry-run through `tenderfinder_raw_sweep.py`

Because sandbox network blocked live HTTP, the same integrated command was run with `--dry-run`:

```bash
python tenderfinder_raw_sweep.py \
  --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx" \
  --preflight-links \
  --preflight-no-search \
  --preflight-output-dir "./link_audit_out_dry" \
  --preflight-timeout 20 \
  --preflight-retries 2 \
  --preflight-workers 6 \
  --dry-run
```

Result: PASS.

Confirmed:

- Preflight ran through `tenderfinder_raw_sweep.py`.
- The real master workbook was read successfully.
- `Source_Register` was detected.
- `URL / Portal` was recognized as a valid URL column alias.
- 68 source rows were loaded.
- 68 URLs were extracted.
- Required output files were created.
- No master workbook backup, write, or save occurred.
- The run ended with: `Preflight-only run complete. No connector sweep or master write was run.`

---

## 3. Integrated preflight output validation

Dry-run output folder:

```text
01 Code / CONNECTOR_SWEEP / link_audit_out_dry
```

Output files created:

| File | Rows | Size |
|---|---:|---:|
| `TENDER_FINDER_Source_Register_URL_Live_Audit.csv` | 68 | 22,883 bytes |
| `TENDER_FINDER_Source_Register_URL_Live_Audit.xlsx` | n/a | 15,809 bytes |
| `TENDER_FINDER_Source_Register_Fix_Queue.csv` | 0 | 337 bytes |
| `TENDER_FINDER_Source_Register_Replacement_Candidates.csv` | 0 | 602 bytes |
| `TENDER_FINDER_Source_Register_Cleaned_For_Script.csv` | 68 | 12,217 bytes |
| `TENDER_FINDER_Link_Check_Run_Log.txt` | n/a | 3,391 bytes |
| `TENDER_FINDER_Link_Check_Debug_Log.txt` | n/a | 10,262 bytes |

Validated output behavior:

- Output folder exists.
- Required CSV files exist.
- XLSX audit file exists.
- Files are non-empty.
- Fix Queue is created.
- Replacement Candidates file exists even with search disabled.
- Original URLs are preserved in `original_url`.
- `final_url_after_redirect` column is present and populated when available. In dry-run it remains the normalized URL because no HTTP request is made.
- Run log and debug log are separate.
- Diagnostic fields are present:
  - `error_type`
  - `error_message`
  - `classification_reason`
  - `safe_to_scrape`
  - `manual_review_required`
  - `retry_count`

---

## 4. URL alias confirmation

Confirmed supported URL aliases include:

- `URL / Portal`
- `URL`
- `Portal`
- `URL/Portal`
- `official_url`
- `primary_url`
- `example_url`
- `secondary_urls`
- `example_relevant_page_or_record_url`

The real master workbook column `URL / Portal` was normalized to `official_url` and passed input validation.

---

## 5. Master workbook protection

Protected workbook:

```text
00 Master / TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx
```

SHA-256 before patch:

```text
ca20abca726a31828a2b6033bd8d44a1b4b94b301854bcf0d0c80afd4e54bc7c
```

SHA-256 after patch/tests:

```text
ca20abca726a31828a2b6033bd8d44a1b4b94b301854bcf0d0c80afd4e54bc7c
```

Result: PASS. Protected master workbook hash is unchanged.

---

## 6. Safety routing confirmation

Patch 4 excludes these from simple scraping unless `--include-broken-sources` is provided:

- `BROKEN_DNS`
- `BROKEN_SSL`
- `BROKEN_404`
- `BROKEN_OTHER`
- `FIX_URL_FIRST`
- `NO_REPLACEMENT_FOUND`

Patch 4 does not automatically delete or treat these as broken:

- `FORBIDDEN_BUT_LIKELY_VALID` = review / connector-safe
- `NEEDS_CONNECTOR_NOT_SIMPLE_SCRAPE` = connector workflow
- `LOGIN_OR_MANUAL` = manual workflow / Run Queue
- `TIMEOUT_RETRY_NEEDED` = retry / review

Original URLs are never silently replaced.

---

## 7. Known limitations

- Live HTTP validation could not be completed in the sandbox because public DNS resolution failed or stalled.
- The integrated dry-run proves runner wiring, workbook reading, alias handling, and output generation, but not real-world URL liveness.
- Full live link preflight must be rerun from a normal TENDER_FINDER office/residential network.
- The source-health gate can only match connector rows to Source Register rows when names or IDs line up closely enough. The current master Source Register does not include the connector `source_id` column.
- Replacement search was not tested because the required command used `--preflight-no-search`.
