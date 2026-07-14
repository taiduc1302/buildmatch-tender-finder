# TENDER_FINDER Patch 5.0 Final Verified Changelog

**Generated:** 2026-06-24T19:27:48  
**Package:** `TENDER_FINDER_Patch_5_0_Final_VERIFIED.zip`

## Purpose
This patch stabilizes the existing Patch 5.0 implementation candidate. It does not add new sources and does not rebuild the project. It fixes reproducibility, regression-test execution, output verification, promotion/dedupe proof, source summary output, and long-path preflight writer verification.

## Functional Fixes
- Regression runner now executes real `tenderfinder_raw_sweep.py` commands instead of placeholder “would execute” checks.
- `--verify-outputs` validates generated workbooks, source summary, demo workbook, and preflight outputs.
- Explicit packaged fixtures were added for Surrey Planning Reports, Township Langley, and Maple Ridge when sandbox DNS/network blocks live endpoints.
- Review workbooks include `review_decision` and source/evidence URL fields.
- `TENDER_FINDER_Run_Source_Summary.csv` includes acceptance columns for source-level proof.
- `--promote-reviewed` is tested on a copied workbook; first run appends ACCEPT rows and second run skips duplicates.
- Link-checker writer supports long output paths in the requested output directory during sandbox/Linux verification.
- Dedupe keys no longer use generic feed/service URLs as project-unique keys.

## Files Modified
- `01 Code/CONNECTOR_SWEEP/tenderfinder_raw_sweep.py`
- `01 Code/CONNECTOR_SWEEP/tenderfinder_live_link_checker.py`
- `01 Code/CONNECTOR_SWEEP/tenderfinder_guards.py`
- `01 Code/CONNECTOR_SWEEP/tests/run_regression.py`
- `PATCH_5_0_FINAL_REPORT.md`
- `PATCH_5_0_CHANGELOG.md`
- `REGRESSION_TEST_REPORT.md`

## Files Added / Regenerated
- `01 Code/CONNECTOR_SWEEP/tests/fixtures/surrey_planning_reports_review_fixture.csv`
- `01 Code/CONNECTOR_SWEEP/tests/fixtures/twp_langley_devactivity_review_fixture.csv`
- `01 Code/CONNECTOR_SWEEP/tests/fixtures/maple_ridge_devapps_review_fixture.csv`
- `test_outputs_p50/surrey_review.xlsx`
- `test_outputs_p50/tol_review.xlsx`
- `test_outputs_p50/maple_ridge_full.xlsx`
- `test_outputs_p50/TENDER_FINDER_Run_Source_Summary.csv`
- `test_outputs_p50/TENDER_FINDER_Demo_Top_Leads.xlsx`
- `test_outputs_p50/preflight_short/`
- `test_outputs_p50/very_long_output_path_for_patch5_validation_that_should_trigger_safe_writer_or_temp_redirect/.../link_audit_out_v7_1_live/`
- `test_outputs_p50/TENDER_FINDER_Master_WRITE_TEST.xlsx`
- `test_outputs_p50/tol_review_for_promote_marked.xlsx`
- `test_outputs_p50/promote_audit_2026-06-24.json`

## Removed From Final Zip
- Nested `01 Code/CONNECTOR_SWEEP.zip` package copy.
- Local `.env.tenderfinder.local` file.
- Python `__pycache__` folders.
- Stale connector-local raw run/log output folders.

## Current Test Result
- `tests/run_regression.py --all`: PASS
- `tests/run_regression.py --verify-outputs --output-dir ../../test_outputs_p50`: PASS
- Surrey rows: 20
- Township Langley rows: 778
- Maple Ridge rows: 879
- Source summary rows: 3
- Promote rows written: 3
- Duplicate rows skipped on second promote: 3

## Known Limitation
Sandbox DNS/network prevents live municipal endpoint proof. The package is reproducible and regression-verified using explicit fixture fallback under network failure. Rerun on a networked TENDER_FINDER Windows machine for live-source proof.
