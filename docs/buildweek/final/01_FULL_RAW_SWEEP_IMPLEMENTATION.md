# Full Raw Development Sweep Implementation (Gap A)

> AI-tool attribution note: this document describes work done by Claude Code during this session. For the full, honest Codex/GPT-5.6/Claude Code contribution breakdown required by the OpenAI Build Week rules, see the README's "AI tool and contributor disclosure" section and `docs/buildweek/final/CLAIMS_LEDGER.md` — this document alone should not be read as claiming Claude Code built the project's core functionality.

## The defect

Before this session, `Refresh Development Data`'s default acquirer
(`default_development_acquirer`, now renamed `diagnostic_preview_acquirer`)
called `tenderfinder_engine.test_source_definition(..., allow_network=True)`,
which returns only a small bounded `normalized_preview` sample (~5 records per
source). The GUI's headline production action was, in effect, powered by a
connector health-check preview, not a real sweep.

## The fix

`tenderfinder_refresh_service.full_sweep_development_acquirer` calls
`tenderfinder_raw_sweep.run_connector` directly — the same fully-paginated,
GUI-independent function the `--review-only` CLI sweep uses. It performs:

* real ArcGIS FeatureServer/MapServer `query` pagination (`query_arcgis_layer`,
  page size 250, retry/backoff on 503/504/timeout, partial-result handling);
* real Opendatasoft v2.1 dataset pagination (`query_ods`);
* real PDF download + multi-page text-table extraction for Surrey's
  Rezoning/DP-in-process reports (`tenderfinder_raw_sweep`'s
  `surrey_planning_reports` handler);
* collection of every eligible lead up to a configurable safe per-source cap
  (`RefreshRequest.max_records_per_source`, default 2000 — real pagination,
  not a fixed small sample).

`diagnostic_preview_acquirer` (the old bounded-preview function) is kept, but
only for source-health/diagnostic use — it is no longer wired to the
production refresh path anywhere in the GUI or CLI.

## Real evidence (see `03_CONTROLLED_LIVE_REFRESH_RESULTS.md` for the full run)

A controlled live sweep against the 8 runtime-eligible development sources
(`max_records_per_source=200`, a deliberately conservative cap for this proof)
fetched **1,439 real records** and normalized **1,209** after dedup — roughly
**290× more than an 8-source × ~5-record preview (~40 records)** would have
returned, and structurally unbounded by any preview limit.

## Tests

`tests/test_buildweek_refresh_service.py` (offline, `tenderfinder_raw_sweep.run_connector`
monkeypatched so no real network I/O runs in CI):

* `test_full_sweep_acquirer_maps_many_leads_not_a_bounded_preview` — 37
  synthetic leads all come back, not a truncated small sample.
* `test_full_sweep_acquirer_respects_max_records_cap`
* `test_full_sweep_acquirer_non_fetch_status_is_not_ok` /
  `..._error_is_not_ok` / `..._exception_is_a_failed_source_not_a_crash`
* `test_make_full_sweep_acquirer_binds_raw_dir_outside_package`
* `test_full_sweep_flow_promotes_dataset_with_many_records` (150-record e2e)
* `test_diagnostic_preview_and_full_sweep_are_distinct_functions` — guards
  against ever re-aliasing the bounded preview back onto the production path.
