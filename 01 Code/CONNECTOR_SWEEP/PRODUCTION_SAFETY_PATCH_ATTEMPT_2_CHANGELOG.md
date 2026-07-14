# TENDER_FINDER Production Safety Patch Attempt 2 Changelog

## Scope

Patched only:

- `tenderfinder_master_io.py`
- `tenderfinder_raw_sweep.py`

Added only:

- `PRODUCTION_SAFETY_PATCH_ATTEMPT_2_CHANGELOG.md`

No Excel files were modified. `tenderfinder_dev_app_endpoints.csv` was not modified. No P3 extractor was created.

## A. Backup hardening

Updated `tenderfinder_master_io.backup(path)` to:

- Resolve the workbook path to an absolute path.
- Create backup directories safely.
- Use short backup filenames to reduce Windows / OneDrive long-path failure risk.
- Try the normal workbook-adjacent `backups` folder first.
- Fall back to `01 Code / CONNECTOR_SWEEP / workbook_backups` if the adjacent backup fails.
- Raise a clear error if all backup attempts fail.
- Stop before workbook load/write/save if backup cannot be created.
- Print backup source and destination paths clearly.

## B. Write target guard

Updated `tenderfinder_raw_sweep.py` so any `--write-master` target must pass a fail-closed guard before write logic:

- Refuses `TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx` by exact filename.
- Refuses paths that appear to target the protected v6 workbook.
- Requires the filename to look like a copied v7/test workbook by containing `v7` or `test`.
- Prints the resolved write target path before write/backup.
- Prints the resolved backup path after a successful backup.
- Does not block the safe target `../../00 Master/v7_TEST.xlsx`.

## C. Record-level write gate

Added CLI options to `tenderfinder_raw_sweep.py`:

- `--min-fit-score`
- `--max-write-per-source`
- `--review-only`

Write gating now happens after records are normalized into leads and before any master workbook operation.

Behavior:

- Leads below `--min-fit-score` are held for review and not written to `Future_Projects`.
- `--max-write-per-source` caps eligible writes per source.
- Held records are marked with `hold_reason`.
- Only `write_eligible=True` leads are sent to the master writer.

## D. Review-only mode

Added `--review-only` output mode.

Review-only mode writes a review file and does not:

- Open the master workbook.
- Call backup.
- Save a workbook.
- Update `Future_Projects`.
- Update `Rejected_Archive`.
- Update `Run_Log` in the master.
- Update `Source_QA` in the master.

Review output columns:

- `source_id`
- `source_name`
- `project_id`
- `municipality`
- `app_no`
- `address`
- `owner/applicant`
- `app_type_stage`
- `scope_summary`
- `fit_score`
- `proposed_route`
- `write_eligible`
- `hold_reason`
- `source_url`

## E. Reporting

Console summary now reports:

- `records_pulled`
- `records_normalized`
- `records_eligible`
- `records_written`
- `records_held_for_review`
- `records_rejected`

## Still forbidden

Until separately approved:

- All-source `--write-master`.
- Tier 2 `--write-master`.
- Any write to production v6.
- Manual/P3 source writes.
- Wrong-layer source writes.
- Real write tests beyond the explicit limited v7/test scope.
