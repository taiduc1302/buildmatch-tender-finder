# TENDER_FINDER Patch 5.10 Build Report

## T0 Surrey Verification

- Verdict: CORRECT application layer, not generic parcel/subdivision boundary metadata.
- Evidence: `docs/SURREY_DEVAPPS_V2_AUDIT.md` includes the full field list and 10 sample rows.
- Fields verified present/populated: `PROJECT_NO`, `DESCRIPTION`, `STATUS`, `WEBLINK`, `APPLICATION_DOCUMENTS_WEBLINK`.
- Volume explanation: Surrey V2 is a broad status-mixed/historical application archive with one geometry row per application/project area. It includes `Concluded` and `Closed` rows, so its 13,737 clean rows should not be interpreted as 13,737 active near-term projects.
- Corrected BID LATER count after Track 0: unchanged for Surrey removal because the layer is not wrong.

## T1 Abbotsford

- Retry backoff changed to 1s/3s/8s for ArcGIS 503/504/timeouts.
- Full sweep result: Abbotsford landed in the all-connector output.
- Abbotsford row count: 503 pulled / 500 clean after 3 duplicate skips.

## T2 Stretch Discovery

- Best effort documented in `PATCH_5_11_BACKLOG.md`.
- No new connector-ready sources were added in Patch 5.10 beyond the Patch 5.9 additions.

## T3 Run-Over-Run Persistence

- `lead_id` generation implemented: YES.
- `demo_history` mechanism working: YES.
- History archive created: `demo_history/demo_p510_20260629_205453.xlsx`.
- `New_This_Run` sheet present: YES, 19,824 rows.
- Baseline note shown correctly: YES, first run had no prior history workbook.

## T4 Outreach Tracker

- `Outreach_Tracker` sheet present: YES.
- Outreach rows: 7,010.
- Merge-forward test: PASS.
- Manual simulation: PASS, a `Contacted` status and notes survived a second build in `tests/test_outreach_persistence.py`.

## T5 Developer Intelligence

- `Developer_Watchlist` sheet present: YES.
- Distinct developers/applicants found: 1,464.
- Repeat developers/applicants with 3+ applications: 284.
- Known major developer names matched: see workbook `Developer_Watchlist`; generated report recorded no special major-name summary in the final console.
- Applicant data caveat: applicant/owner fields are sparse across several municipal sources; the sheet uses real exposed source fields only.

## T6 Tender Pattern

- `Tender_Pattern_Analysis` sheet present: YES.
- Caveat included: YES.
- Sample size: 16 civil-relevant tender signals in the live public-page sweep; 0 open civil tenders.

## T7 Scale Tiering

- `project_scale_tier` column present in BID LATER and Top 50: YES.
- Distribution: LARGE=162, MEDIUM=891, SMALL=2,870, UNKNOWN=15,901.
- Dollar estimates: none generated; raw currency-like source text was scrubbed from workbook outputs.

## T8 Geographic Clustering

- `regional_cluster` column present in BID LATER and Top 50: YES.
- Counts by cluster: Fraser Valley East=500, Other=582, South of Fraser=14,991, Tri-Cities=454, Vancouver=3,297.

## T9 Final Run

- Full sweep output: `C:\tenderfinder_out\patch5_10_live\all_live_review.xlsx`.
- Records pulled: 41,508.
- Records normalized: 33,618.
- Corrected Track A counts: BID LATER=19,824 / Watchlist=973 / Analyzed=12,832.
- BID NOW: 29 total / 16 civil-relevant / 0 open civil / 16 with contact.
- Workbook: `C:\tenderfinder_out\demo_p510\TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx`.
- Workbook quality tests: 5/5 pass.
- Email fixture tests: 4/4 pass.
- Outreach persistence test: PASS.
- Regression: 24/26 pass; only the known long preflight output-path checks failed.
- v6 SHA: MATCH `CA20ABCA726A31828A2B6033BD8D44A1B4B94B301854BCF0D0C80AFD4E54BC7C`.
- v7_1 SHA: MATCH `A1DD67E0C62473B1CE9F5E46A8F8A3FAFF3A866E716BB96C33C848D217941F3D`.

## T10 Autonomous Fixes

- Audited Surrey V2 with live field/sample evidence.
- Hardened ArcGIS retry backoff.
- Added stable lead IDs and address normalization.
- Added demo history archiving and New_This_Run.
- Added Outreach_Tracker with merge-forward behavior and test coverage.
- Added Developer_Watchlist, Tender_Pattern_Analysis, project_scale_tier, and regional_cluster.
- Added workbook no-currency QA and scrubbed currency-like source text from final workbook outputs.
