# TENDER_FINDER Patch 5.9 Build Report

## T0 PRECHECK

- Track A baseline: confirmed at 5,393 Future_Projects / 999 Run_Queue / 12,766 analyzed in `baseline_p59.json`.
- Fresh regression: 22/24 pass at `C:\tenderfinder_out\regression_p59_final2\REGRESSION_TEST_REPORT.md`.
- Regression failure status: pre-existing long-output preflight failure only; core compile, list, parser, routing, review, promote, and dedupe checks passed.
- Gmail STATE: A. 64 canonical-domain emails detected, 1 tender-term candidate read, 0 real tender-alert rows parsed.
- Hard boundaries: no Working_Master / v6 / v7_1 writes, no portal login, no fixtures used as live proof.

## T1 BID NOW CLEANUP

- `.pdf` title with `civil_relevant=NO`: filtered.
- `contact_phone` values matching `^\d{4}-\d{3}-\d{4}$`: cleared.
- Richmond page-title row without closing date: filtered.
- Tests updated in `01 Code/CONNECTOR_SWEEP/tests/test_workbook_quality.py`.

## T2 NEW CONNECTORS

- `surrey_devapps_v2`: LIVE | 13,749 pulled | 13,737 clean | 0 watch | 0 rejected | `https://services5.arcgis.com/YRpe0VKTJytZSSIB/arcgis/rest/services/Development%20Applications/FeatureServer/0`
- `abbotsford_devapps`: LIVE standalone proof | 503 pulled | 500 clean | 0 watch | 0 rejected | `https://services8.arcgis.com/ZYlQy38aWlfDG1Qh/arcgis/rest/services/Development_Layers_External_Feature/FeatureServer/6`
- `new_west_currentdev`: NOT_CONNECTED | exact Current Developments layer not found; raw runner resolves building/plumbing permits only.
- `burnaby_devapps`: NOT_FOUND | Hub/DCAT did not expose development or rezoning application records.
- `delta_devapps`: TRAILING_CONTEXT | Building Permits only; no current development application layer found.
- `city_langley_devapps`: NOT_FOUND | Hub/DCAT did not expose application records.
- `van_rezoning`: NOT_FOUND | guessed ODS slug 404 and catalog search empty.
- `van_devpermits`: NOT_FOUND | guessed ODS slug 404 and catalog search empty.
- `dnv_devapps`: NOT_FOUND | infrastructure/DPA/reference layers only.
- `port_coquitlam_landdev`: NOT_FOUND | OCP/zoning/ROW/reference layers only.

## T3 NEW SOURCE DISCOVERIES

- Port Moody: probed, no connector-ready development-application layer found.
- Mission: probed, no connector-ready development-application layer found.
- Chilliwack: probed, no connector-ready development-application layer found.
- White Rock: probed, no connector-ready development-application layer found.
- Township Langley: existing connector remains optimal for this patch.
- BC Data Catalogue: searched; no connector-ready aggregate municipal development-application dataset found.

## T4 SCORING

- `source_tier` column added to BID LATER output.
- New connector rows are marked tiered by source ID; Surrey DevApps V2 and Abbotsford default to `TIER_2`.
- No routing thresholds or write gates were changed to inflate counts.

## T5 SWEEP + TESTS

- Full sweep output: `C:\tenderfinder_out\patch5_9_live\all_live_review.xlsx`
- Source summary: `C:\tenderfinder_out\patch5_9_live\TENDER_FINDER_Run_Source_Summary.csv`
- Full sweep records pulled: 41,005.
- Full sweep records normalized: 33,118.
- New Track A counts from review workbook: BID LATER=19,324 / Watchlist=974 / Analyzed=12,832.
- Count reconciliation note: source summary reports 967 scored watchlist rows; review workbook has 974 `Run_Queue` rows because 7 manual/P3 connector stubs are also represented as Run_Queue rows.
- Net new clean leads vs baseline: +13,931.
- Demo workbook: `C:\tenderfinder_out\demo_p59\TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx`
- Demo BID NOW: 27 total / 14 civil-relevant / 0 open civil / 15 with contact email or phone.
- Regression: 22/24 pass, with pre-existing long-output preflight failure.
- v6 SHA: MATCH `CA20ABCA726A31828A2B6033BD8D44A1B4B94B301854BCF0D0C80AFD4E54BC7C`
- v7_1 SHA: MATCH `A1DD67E0C62473B1CE9F5E46A8F8A3FAFF3A866E716BB96C33C848D217941F3D`

## T6 DEMO MATERIALS

- `demo_p59/DEMO_TALKTRACK.md`: regenerated with Patch 5.9 counts and email intake live language.
- `demo_p59/DEMO_BUILD_REPORT.md`: regenerated.
- `demo_p59/demo_summary.txt`: regenerated.
- Executive Summary: updated to show current full-sweep pulled/normalized counts, live source count, and municipality count.
- Action Center: retained no-login guidance and portal registration path.
- `run_tenderfinder_demo.bat`: updated to Patch 5.9 review/output paths.

## T7 AUTONOMOUS_FIXES

- Added Excel illegal-character stripping for ArcGIS text output.
- Added ArcGIS retry handling for transient 503/service-unavailable responses.
- Added `surrey_devapps_v2` source registry alias and endpoint CSV row while leaving legacy `surrey_devapps` untouched.
- Added `abbotsford_devapps` live endpoint metadata.
- Added `source_tier` to BID LATER.
- Added BID NOW junk filters and workbook quality assertions for Patch 5.9 cleanup cases.

## Remaining Warnings

- Abbotsford is live-proven standalone but did not land in the full all-connector review workbook because the full sweep hit a transient ArcGIS 503 at that source.
- BID NOW remains honest but thin: public pages yielded 0 open civil tenders; dense bid-ready tender volume still depends on registering for portal email alerts and enabling civil alert categories.
- New Westminster, Burnaby, City Langley, Vancouver rezoning/dev permits, DNV, Port Coquitlam, and bonus municipalities need Patch 5.10/P3/manual source discovery.
