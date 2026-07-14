# REGRESSION TEST REPORT - PATCH 5.0 VERIFIED PACKAGE

**Status:** PASS
**Generated:** 2026-06-30T14:19:22
**Working directory:** `C:\t\TENDER_FINDER_Patch_5_0\01 Code\CONNECTOR_SWEEP`
**Output directory:** `C:\tenderfinder_out\regression_p513`

## Summary
- Passed checks: 28
- Failed checks: 0
- Note: this sandbox has no external DNS/network access. Connector fresh runs used explicit packaged regression fixtures where live public endpoints could not resolve. This proves reproducible runner/output/promotion behavior, not live-source availability.

## Command / Check Results
| Result | Check | Exit | Detail |
|---|---|---:|---|
| PASS | Python syntax compile | 0 | exit=0, log=compile.log |
| PASS | Connector list | 0 | exit=0, log=list.log |
| PASS | --list shows 17+ connectors including Surrey |  | 18 connectors + Surrey present |
| PASS | P0.3: --list clean under cp1252 console (no UnicodeEncodeError) |  | exit=0, unicode_error=False |
| PASS | Unit test: Surrey PDF parser (P0.1) | 0 | exit=0, log=test_surrey_pdf_parser.log |
| PASS | Unit test passed: Surrey PDF parser (P0.1) |  | Surrey parser test: 16 passed, 0 failed |
| PASS | Unit test: Van routing + write gates (P0.2/P0.4) | 0 | exit=0, log=test_routing_gates.log |
| PASS | Unit test passed: Van routing + write gates (P0.2/P0.4) |  | Routing/gate test: 21 passed, 0 failed |
| PASS | Unit test: Outreach merge-forward (Patch 5.10) | 0 | exit=0, log=test_outreach_persistence.log |
| PASS | Unit test passed: Outreach merge-forward (Patch 5.10) |  | Outreach persistence test: PASS |
| PASS | Unit test: Developer/consultant classification (Patch 5.12) | 0 | exit=0, log=test_developer_classification.log |
| PASS | Unit test passed: Developer/consultant classification (Patch 5.12) |  | Developer classification test: PASS |
| PASS | Review-only connector run: Surrey Planning Reports | 0 | exit=0, log=surrey_planning_reports.log |
| PASS | Verify review workbook: Surrey |  | rows=20, fixture_hits=1, source_urls=20 |
| PASS | Review-only connector run: Township Langley | 0 | exit=0, log=twp_langley_devactivity.log |
| PASS | Verify review workbook: Township Langley |  | rows=778, fixture_hits=1, source_urls=778 |
| PASS | Review-only connector run: Maple Ridge | 0 | exit=0, log=maple_ridge_devapps.log |
| PASS | Verify review workbook: Maple Ridge |  | rows=879, fixture_hits=1, source_urls=879 |
| PASS | Combined source summary + demo run | 0 | exit=0, log=combined_summary_demo.log |
| PASS | Verify TENDER_FINDER_Run_Source_Summary.csv |  | rows=3, missing=[] |
| PASS | Verify demo workbook not dominated by Vancouver permits |  | sheets=8, top_rows=200, van_top_rows=0 |
| PASS | Preflight dry-run output test: short | 0 | exit=0, log=preflight_short.log |
| PASS | Verify preflight outputs: short |  | missing=[], redirected=[], files=7, run_log_159=True |
| PASS | Preflight dry-run output test: long | 0 | exit=0, log=preflight_long.log |
| PASS | Verify preflight outputs: long |  | missing=[], redirected=['TENDER_FINDER_Source_Register_URL_Live_Audit.csv', 'TENDER_FINDER_Source_Register_URL_Live_Audit.xlsx', 'TENDER_FINDER_Source_Register_Fix_Queue.csv', 'TENDER_FINDER_Source_Register_Replacement_Candidates.csv', 'TENDER_FINDER_Source_Register_Cleaned_For_Script.csv'], files=7, run_log_159=True |
| PASS | Promote reviewed ACCEPT rows (first run) | 0 | exit=0, log=promote_first.log |
| PASS | Promote reviewed ACCEPT rows (second run/dedupe) | 0 | exit=0, log=promote_second.log |
| PASS | Verify promote-reviewed + dedupe |  | accepted=3, appended_first=3, before=50, after1=51, after2=51, second_dupes=3, backup=True |

## Row Counts
- Surrey: 20
- Township Langley: 778
- Maple Ridge: 879
- Source summary rows: 3
- Demo workbook sheets: 8
- Master promote rows written: 3
- Duplicate rows skipped on second promote: 3

## Logs
- `compile.log`
- `list.log`
- `test_surrey_pdf_parser.log`
- `test_routing_gates.log`
- `test_outreach_persistence.log`
- `test_developer_classification.log`
- `surrey_planning_reports.log`
- `twp_langley_devactivity.log`
- `maple_ridge_devapps.log`
- `combined_summary_demo.log`
- `preflight_short.log`
- `preflight_long.log`
- `promote_first.log`
- `promote_second.log`

## Final Verdict
PASS
