# TENDER_FINDER Patch 5.4 Live Proof Report

Generated: 2026-06-25T15:56:30

## Executive Summary

Patch 5.4 live proof completed without fixture fallback and without writing to the protected v6 or v7_1 master workbooks. The refreshed all17 review-only run pulled 27,260 live records, normalized 19,146 rows, produced 5,393 clean Future_Projects candidates, kept 992 watchlist records reviewable, held 5,832 bulk records, preserved 6,934 rejected/context/wrong-layer records, and kept 7 manual/P3 connector rows visible.

Surrey is now live-proven against current PDFs with 794 extracted planning-report rows. Township Langley and Maple Ridge remain live-proven core sources. Coquitlam was added as a low-risk Patch 5.4 connector improvement and live-proven with 471 pulled / 452 clean rows. Vancouver permits remain useful but noisy: only 3,107 rows are clean eligible after dedupe/gating, while watchlist/bulk/noisy records stay reviewable and do not contaminate clean leads.

## Commands Run

- `python tenderfinder_raw_sweep.py --only surrey_planning_reports --review-only --out "C:\tenderfinder_out\patch5_4_live\surrey_live_review.xlsx"` -> exit 0; output `C:\tenderfinder_out\patch5_4_live\surrey_live_review.xlsx`; pulled=794, normalized=794, clean=794, watchlist=0, bulk=0, rejected=0, fixture_fallback=no, protected_master_touched=no.
- `python tenderfinder_raw_sweep.py --only van_building_permits --review-only --out "C:\tenderfinder_out\patch5_4_live\van_permits_live_review.xlsx"` -> exit 0; output `C:\tenderfinder_out\patch5_4_live\van_permits_live_review.xlsx`; pulled=20000, normalized=16860, clean=3107, watchlist=992, bulk=5832, rejected=6929, fixture_fallback=no, protected_master_touched=no.
- `python tenderfinder_raw_sweep.py --only twp_langley_devactivity,maple_ridge_devapps --review-only --out "C:\tenderfinder_out\patch5_4_live\core_live_review.xlsx"` -> exit 0; output `C:\tenderfinder_out\patch5_4_live\core_live_review.xlsx`; pulled=1689, normalized=1040, clean=1040, watchlist=0, bulk=0, rejected=0, fixture_fallback=no, protected_master_touched=no.
- `python tenderfinder_raw_sweep.py --only coquitlam_devapps --review-only --out "C:\tenderfinder_out\patch5_4_live\coquitlam_live_review.xlsx"` -> exit 0; output `C:\tenderfinder_out\patch5_4_live\coquitlam_live_review.xlsx`; pulled=471, normalized=452, clean=452, watchlist=0, bulk=0, rejected=0, fixture_fallback=no, protected_master_touched=no.
- `python tenderfinder_raw_sweep.py --review-only --out "C:\tenderfinder_out\patch5_4_live\all17_live_review.xlsx"` -> exit 0; output `C:\tenderfinder_out\patch5_4_live\all17_live_review.xlsx`; pulled=27260, normalized=19146, clean=5393, watchlist=992, bulk=5832, rejected=6934, fixture_fallback=no, protected_master_touched=no.
- `python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7_1_cleaned_urls.xlsx" --preflight-links --preflight-no-search --preflight-output-dir "C:\tenderfinder_out\patch5_4_live\preflight_159_live" --preflight-timeout 20 --preflight-retries 2 --preflight-workers 6` -> exit 0; output `C:\tenderfinder_out\patch5_4_live\preflight_159_live`; pulled=159, normalized=159, clean=59, watchlist=17, bulk=0, rejected=36, fixture_fallback=no, protected_master_touched=no.

## Acquisition Funnel

| Metric | Count | Basis |
| --- | ---: | --- |
| Source Universe count | 159 | Source_Register rows from v7_1 preflight |
| Source Register coverage | 159 | 159/159 rows classified |
| Coded connector count | 17 | tenderfinder_dev_app_endpoints all17 run |
| Working live automated sources | 5 | Loaded with live pulled records |
| Semi-automated / PDF candidates | 10 | Source coverage bucket |
| Semi-automated / RSS / HTML / platform candidates | 62 | Source coverage bucket |
| Manual / P3 / login / paid sources | 49 | Source coverage bucket |
| Records pulled | 27260 | all17 live source summary |
| Records normalized | 19146 | all17 live source summary |
| Clean TENDER_FINDER candidates | 5393 | Future_Projects clean only |
| Watchlist candidates | 992 | Run_Queue/watchlist rows |
| Bulk/noisy records | 12766 | Bulk_Intake_Raw plus Rejected_Archive/context rows |
| Rejected/context records | 6934 | Rejected_Archive rows |
| Failed/manual sources | 9 | Connector entries requiring non-live or repair workflow |
| Safe-to-promote rows | 3 | ACCEPT rows in core_live_review_ACCEPT_sample.xlsx |

## Connector Status Counts

- live_context_or_rejected: 3
- live_working: 5
- manual_or_p3_stub: 7
- wrong_layer_disabled: 2

## Counts Reconciliation Note

- The all17 run totals are post-dedupe/routing metrics. `clean + watchlist + bulk + rejected = 5,393 + 992 + 5,832 + 6,934 = 19,151`, while `records_normalized = 19,146`. The five-row difference is expected from connector-level summary dimensions that include manual/context stub rows and route-level rollups separately from normalized candidate rows. The source summary remains the authority for each connector's row counts.
- Vancouver permit tiering has two valid views: raw tier filter output (`strong=3,143`, `watchlist=1,215`, `bulk=6,034`, `noisy=9,608`, sum `20,000`) and post-dedupe routed output (`clean=3,107`, `watchlist=992`, `bulk=5,832`, `rejected/noisy=6,929`, sum `16,860`). The difference is caused by 3,140 within-run duplicate app/address rows and route gating; bulk/noisy records remain reviewable and are not clean leads.
- Source Register preflight status counts (`40 OK`, `19 redirected`, `17 connector-required`, `42 manual/login`, `36 broken`) are URL audit statuses. Source coverage buckets are workflow classifications, so some broken or blocked platform URLs are counted under connector/manual workflow buckets rather than only `broken_or_replaced`.

## Source Register Coverage Buckets

- broken_or_replaced: 29
- email_or_gc_invite_workflow: 8
- login_required: 5
- manual_p3: 28
- paid_intelligence: 8
- semi_automated_pdf: 10
- semi_automated_rss_html: 62
- working_live_automated: 9

## Promote Proof

Copied test master: `C:\tenderfinder_out\patch5_4_live\TENDER_FINDER_Master_PATCH5_4_WRITE_TEST.xlsx`

Review sample: `C:\tenderfinder_out\patch5_4_live\core_live_review_ACCEPT_sample.xlsx`

First promote run: ACCEPT=3, REJECT=1, HOLD=1, blank=1035; appended=3; backup created at `C:\tenderfinder_out\patch5_4_live\backups\TENDER_FINDER_Master_PATCH5_4_WRI_20260625_154542.bak.xlsx`.

Second promote run: appended=0; duplicates_skipped_on_write=3; backup created at `C:\tenderfinder_out\patch5_4_live\backups\TENDER_FINDER_Master_PATCH5_4_WRI_20260625_154552.bak.xlsx`; audit exists at `C:\tenderfinder_out\patch5_4_live\promote_audit_2026-06-25.json`.

Protected v7_1 SHA-256 after proof: `A1DD67E0C62473B1CE9F5E46A8F8A3FAFF3A866E716BB96C33C848D217941F3D`.

Protected v6 SHA-256 after proof: `CA20ABCA726A31828A2B6033BD8D44A1B4B94B301854BCF0D0C80AFD4E54BC7C`.

## Remaining Risks

- Several connector entries are honest stubs or disabled/wrong-layer entries and should not be called live-working.
- The 159-source preflight found 36 broken URLs that require owner review or replacement.
- Active tender portals such as BC Bid, Bonfire, MERX, and bidsandtenders need platform-specific connector or manual/login workflows.
- Vancouver permits are high-volume but noisy; only the gated clean subset should move toward review/promote.
