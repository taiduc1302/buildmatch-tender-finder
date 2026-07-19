# Live Development Refresh and Rollback

Module: `tenderfinder_refresh_service.py` (headless, injectable, fully tested).

## The flow (`refresh_development_data`)

1. Select eligible development-track sources from the truthful registry
   (`eligible_development_sources`). Excludes `manual_only`,
   `needs_configuration`, `wrong_source`, `blocked`, `config_valid_only`,
   `deprecated`, and disabled sources.
2. Acquire per-source via a **safe acquirer** (`default_development_acquirer`
   uses the engine's guarded single-source live test, which enforces URL-safety
   and never contacts login/blocked sources). Each source yields a `SourceFetch`
   with ok/records/error/http_status.
3. Collect per-source outcomes and counts.
4. Normalize and **deduplicate** (`deduplicate_records`) by
   (source, app_no/lead_id, address/title/url).
5. **Validate** the dataset (`validate_dataset`): non-empty, descriptive fields.
6. Write a timestamped external dataset (`development_review_<run>.xlsx`).
7. **Promote atomically** as the active dataset (`data_modes.promote_dataset`) —
   validation runs before the pointer is swapped.
8. **Score** the promoted dataset into a ranked output workbook (injected scorer;
   the GUI uses the engine).
9. Write a run manifest and return a truthful `RunMetrics`.

## Failure behaviour (last-known-good rollback)

`_failure(...)` is taken on total source failure, empty acquisition, failed
dataset validation, or refused promotion. In every case:

- the previous active dataset pointer is **left untouched**;
- the previous dataset is re-labelled cached/stale (`data_modes.mark_stale`; a
  previously LIVE dataset becomes CACHED_LIVE — never stays LIVE);
- the last-successful-refresh timestamp is **not advanced**;
- the failed run's metrics report `succeeded=False` and **no live records**;
- the packaged synthetic input is never touched or presented as live.

## Tested scenarios (`tests/test_buildweek_refresh_service.py`)

- eligible-source exclusion of non-runnable sources;
- full flow → promotion → scoring → manifest → reconciled metrics;
- partial source failure still produces a dataset with truthful failure counts;
- total failure preserves the previous dataset and marks it stale;
- failed validation preserves the previous dataset;
- dedup reconciliation;
- datasets are never written inside the package.
