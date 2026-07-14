# BULK HARVEST PATCH ATTEMPT 3 CHANGELOG

## Purpose

Patch Attempt 3 changes the next workflow from curated-first writing to a bulk data acquisition mode.

The new mode is designed to pull selected sources broadly and write raw/normalized records into a dedicated workbook sheet named `Bulk_Intake_Raw` inside a copied test/bulk master workbook. It does not use `Future_Projects` as the raw dump.

## Base Package

Base used for this patch:

`TENDER_FINDER_production_safety_patch_attempt_2.zip`

## Files Changed

Patched:

- `01 Code / CONNECTOR_SWEEP / tenderfinder_raw_sweep.py`

Added:

- `01 Code / CONNECTOR_SWEEP / tenderfinder_bulk_io.py`
- `01 Code / CONNECTOR_SWEEP / BULK_HARVEST_PATCH_ATTEMPT_3_CHANGELOG.md`

Not modified:

- `00 Master / TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx`
- `01 Code / CONNECTOR_SWEEP / tenderfinder_dev_app_endpoints.csv`
- all Excel source files
- all prompt files
- all research files
- all existing runbooks
- `_ss`

## New CLI Mode

Added:

```bash
--bulk-intake
```

Default behavior:

- pulls selected sources normally
- writes broad acquisition rows to `Bulk_Intake_Raw`
- does not write to `Future_Projects`
- does not write to `Rejected_Archive`
- includes manual/P3/access-test/error sources as stub rows when no pull is possible

## New CLI Options

Added:

```bash
--bulk-intake
--promote-to-future-projects
--also-write-rejected
--include-tier2
--include-tier3
--include-trailing-context
--include-wrong-layer
--max-records-per-source
```

## Bulk_Intake_Raw Columns

The new sheet uses these columns:

- `run_id`
- `run_timestamp`
- `source_id`
- `source_name`
- `tier`
- `municipality`
- `access_status`
- `fetch_type`
- `resolved_endpoint`
- `records_pulled`
- `record_index`
- `classification`
- `output_route`
- `status`
- `richness`
- `project_id`
- `application_no`
- `address`
- `owner_applicant`
- `application_type_stage`
- `scope_summary`
- `fit_score`
- `source_url`
- `raw_json`
- `raw_file_path`
- `error`
- `notes`

## Promotion Rules

`--bulk-intake` does not promote records to `Future_Projects` by default.

Promotion only happens when this option is provided:

```bash
--promote-to-future-projects
```

Rejected/wrong-layer/thin/context summaries are not appended to `Rejected_Archive` by default.

Rejected writes only happen when this option is provided:

```bash
--also-write-rejected
```

## Safety Rules Preserved

- Protected v6 write is refused before pull, backup, workbook load, or save.
- Write target must look like a copied `v7`, `test`, or `bulk` workbook.
- Backup is still mandatory before save.
- If backup fails, the workbook write fails closed.
- The resolved write target is printed before backup.
- The resolved backup path is printed after backup.
- No P3 extractor was created.
- No production v6 write was run.
- No all-source real write was run during patch creation.

## Reporting Added

Bulk mode prints source-level and total summary fields:

- `selected`
- `pulled`
- `written_to_bulk_intake`
- `promoted_to_future_projects`
- `rejected_written`
- `skipped`
- `errors`

## Required Tests Run

All tests were run against a copied/extracted test folder, not the production v6 workbook.

### 1. Compile

Command:

```bash
python -m py_compile tenderfinder_raw_sweep.py tenderfinder_master_io.py tenderfinder_guards.py tenderfinder_source_registry.py tenderfinder_bulk_io.py
```

Result: OK.

### 2. Help

Command:

```bash
python tenderfinder_raw_sweep.py --help
```

Result: OK. New bulk options are shown.

### 3. List

Command:

```bash
python tenderfinder_raw_sweep.py --list
```

Result: OK. 16 connectors listed.

### 4. V6 Write Refusal

Command:

```bash
python tenderfinder_raw_sweep.py --bulk-intake --only twp_langley_devactivity --max-records-per-source 1 --write-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx"
```

Result: OK. Protected v6 was refused before pull/write.

### 5. Tier 1 Bulk Dry-Run

Command:

```bash
python tenderfinder_raw_sweep.py --bulk-intake --tier 1 --dry-run --max-records-per-source 50
```

Result: OK.

Sandbox network/DNS limitation prevented live TOL/MR pulls in this environment. The dry-run still confirmed stub handling and no workbook open/backup/save.

Observed summary:

- selected: 5
- pulled: 0
- would_write_to_bulk_intake: 5
- promoted_to_future_projects: 0
- rejected_written: 0
- skipped: 5
- errors: 2

### 6. Limited Real Write to Copied Test Workbook

Command:

```bash
python tenderfinder_raw_sweep.py --bulk-intake --tier 1 --max-records-per-source 50 --write-master "../../00 Master/v8_BULK_INTAKE_TEST.xlsx"
```

Result: OK.

Observed summary:

- copied test workbook created from v6
- backup created
- workbook saved
- `Bulk_Intake_Raw` created
- `Bulk_Intake_Raw`: appended 5 rows
- `Future_Projects`: not promoted
- `Rejected_Archive`: not written

Network/DNS limitation prevented live TOL/MR pulls, so the real write test wrote Tier 1 stub/error rows only. No production workbook was touched.

## Current Limitations

- Live bulk harvest from TOL/MR could not be fully verified in this sandbox because external host resolution failed.
- `Bulk_Intake_Raw` can grow quickly; use copied test/bulk workbooks only.
- `raw_json` is stored in Excel cells and is truncated when needed to stay Excel-safe.
- `--promote-to-future-projects` still relies on the current rule-based normalized lead logic and should remain optional.
- `--also-write-rejected` remains optional to avoid polluting `Rejected_Archive` during pure harvest/debug runs.

## Recommended Next Command Outside Sandbox

Use a copied workbook only:

```bash
python tenderfinder_raw_sweep.py --bulk-intake --tier 1 --max-records-per-source 100 --write-master "../../00 Master/v8_BULK_INTAKE_TEST.xlsx"
```

Do not use the protected production v6 workbook.
