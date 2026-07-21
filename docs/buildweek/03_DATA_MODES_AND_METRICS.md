# Data Modes and Truthful Metrics

Module: `tenderfinder_data_modes.py`.

## Data modes

| Mode | Banner |
|---|---|
| `SYNTHETIC` | `SYNTHETIC DEMO DATA — no real opportunities` |
| `PUBLIC_SNAPSHOT` | `PUBLIC SNAPSHOT — captured <date>` |
| `LIVE` | `LIVE PUBLIC DATA — refreshed <date> at <time>` |
| `CACHED_LIVE` | `CACHED LIVE DATA — last successful refresh <age>` |
| `MIXED` | `MIXED DATA — live and synthetic rows are present` |
| `UNKNOWN` | `UNKNOWN DATA ORIGIN — review before use` |

Rules enforced in code and tests:

- synthetic-only can never be classified `LIVE` (`classify_record_counts`);
- a failed refresh cannot advance the live timestamp (`mark_stale`);
- mixed cannot become pure live;
- unknown origin shows a warning banner;
- snapshot shows the capture date and source provenance.

The banner is shown in the GUI, run summaries, manifests, logs, exports, and the
AI-analysis provenance block, all from the one `DatasetProvenance` contract.

## Active-dataset pointer

`active_dataset.json` under `<state-root>/datasets/` with:

- atomic write (`atomic_write_json` → temp + `os.replace`);
- validation before promotion (`validate_provenance_for_promotion`);
- previous pointer retained on failure and backed up to `active_dataset.json.bak`;
- corrupted-pointer recovery from the backup;
- missing-pointer recovery (returns `None`, GUI falls back to the synthetic banner);
- never overwrites the packaged synthetic input.

## Truthful current-run metrics (`RunMetrics`)

Every field describes the **current** operation. Historical totals never populate
current-run fields. The contract reconciles itself (`reconciliation_errors`):

- `records_before_dedup == records_fetched + records_loaded`
  (a replayed workbook counts as *loaded*, not *fetched*; zero fetched stays zero);
- `normalized_records == records_before_dedup − duplicates_removed`;
- `bid_now + bid_later + watch + skip == records_scored`;
- per-origin breakdown reconciles to `normalized_records`;
- a failed run cannot report fetched/live records as its own result.

The GUI/CLI/manifest/logs all consume the same serialized `RunMetrics`, so a
displayed number always belongs to the run it labels. Tests in
`tests/test_buildweek_data_modes.py` prove each invariant, including that a
stray historical field cannot leak through `RunMetrics.from_dict`.
