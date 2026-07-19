# Final Change Index (This Session)

Base: PR #3 head `5d155e027afa3b17826c352e18df97bdfa5a8c92` (the prior
session's completed work, preserved in full — nothing discarded).

## Commits added this session

1. `5319a7d` — fix: real full-sweep refresh, user-selected AI record, Self-Test coverage
2. `fab8112` — fix: real deterministic scoring wired into refresh + truthful-metrics ordering
3. `be980ca` — feat: upgrade Public Snapshot demo with a real 82-record live sample
4. `08691dc` — fix(security): neutralize Excel formula-injection in refresh-service output

(A final documentation commit follows this index.)

## Product code

- `tenderfinder_refresh_service.py` — `full_sweep_development_acquirer`,
  `make_full_sweep_acquirer`, `default_scorer`, `make_default_scorer`,
  `_lead_to_record`, `diagnostic_preview_acquirer` (renamed from
  `default_development_acquirer`, kept as a back-compat alias); fixed
  `deduplicate_records`/`validate_dataset` (thin-stub handling);
  fixed `records_live` ordering; formula-injection guard on both writers.
- `tenderfinder_data_modes.py` — relaxed `RunMetrics.reconciliation_errors()`
  failed-run invariant to check `records_live` specifically.
- `tenderfinder_engine.py` — added the 6 Build Week suites to
  `SELF_TEST_SCRIPTS`.
- `tenderfinder_launcher_gui.py` — new `ranked_opportunities()`,
  `resolve_selected_opportunity()`, `opportunity_row_values()`; new
  `opportunities_tab` (`ttk.Treeview` ranked-opportunity table + selection +
  detail panel); rewired refresh worker to use the full-sweep acquirer + real
  scorer; rewired AI action to require a genuine selection, with a separate
  explicitly-labelled "Analyze Top-Ranked Opportunity" convenience action.

## Configuration

- `requirements.txt`, `01 Code/CONNECTOR_SWEEP/requirements.txt` — declared
  `openai>=1.50` (previously undeclared despite being required).

## Data

- `demo_data/public_snapshot/development_snapshot.csv`,
  `snapshot_manifest.json`, `generate_snapshot.py` — replaced with 82 real,
  sanitized public records from the controlled live sweep.

## Tests

- `01 Code/CONNECTOR_SWEEP/tests/test_buildweek_refresh_service.py` — +23
  tests (full-sweep acquirer behaviour, real scorer, thin-record handling,
  truthful-metrics regression, formula-injection).
- `01 Code/CONNECTOR_SWEEP/tests/test_buildweek_gui_helpers.py` — +7 tests
  (ranked-opportunity selection, no-silent-substitution).

## CI / packaging

- `scripts/windows_acceptance.ps1` — rewritten with `Invoke-Step` so a
  failed step can no longer be silently swallowed by a false "PASS" banner.

## Documentation

- `docs/buildweek/05_OPENAI_GUI_INTEGRATION.md`,
  `docs/buildweek/07_THREE_MINUTE_DEMO.md` — corrected the "auto-picks the
  top-ranked record" claim and the 8-fictitious-record snapshot description.
- `docs/buildweek/final/00-10` (this set) — new.

## Net effect on the mandatory test gates

| Gate | Before this session | After this session |
|---|---|---|
| Full offline pytest | 194 passed, 8 skipped, 0 failed | 216 passed, 8 skipped, 0 failed |
| Authoritative Self-Test | 106 passed (Build Week suites not wired in) | 198 passed, 0 failed |
| Package audit | PASS | PASS |
| Clean release build + verify | PASS | PASS |
