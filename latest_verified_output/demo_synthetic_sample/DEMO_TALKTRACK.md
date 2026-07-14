# TENDER_FINDER Demo Talk Track

## OPENING

1. TENDER_FINDER is a civil opportunity intelligence pipeline: it pulls municipal signals, scores them for civil/earthworks fit, and routes them into BID NOW, BID LATER, or ANALYZED AND SET ASIDE.
2. This run pulled 27,260 records from 3 live working sources across 3 municipalities in 8.08 seconds, with 6 clean future-project leads ready for review.

## BID NOW

3. Track B performed a parallel live public tender scan across 22 public pages without logging into bidsandtenders.ca, Bonfire, MERX, BC Bid, Ariba, or Jaggaer.
4. Result: 0 actionable BID NOW tenders, 0 civil-relevant, and 0 open civil opportunities. BC Bid open civil: 0; BC Bid status: SKIPPED_NO_FETCH.
5. If BID NOW is thin, explain it plainly: Patch 5.13 verified BC Bid's public browse currently stops at a browser-check/reCAPTCHA wall before any opportunities API is exposed. The Action_Center and docs/BC_BID_NETWORK_AUDIT.md show the compliant next step.

- Track B found public tender candidates, but none scored civil-relevant after deep parsing. This is honest public-page output; Patch 5.6 platform connectors remain the dense BID NOW unlock.

## BID LATER - TOP LEADS

6. BID LATER is the strategic pipeline: 6 clean development-application and future-project leads, including 6 priority rows with fit score >= 60 and 5 top-tier rows with fit score >= 70. Patch 5.13 keeps those corrected Track A routing counts unchanged while adding a real-browser BC Bid audit.
7. Strong future-project examples:
- Exampleville DA-2026-0101 at 100 Demo Street: fit 86, unknown. Proposed 45-lot single family subdivision requiring full onsite/offsite servicing: roads, watermain, storm and sanitary sewers.
- Testburg PL-2026-0301 at 500 Placeholder Way: fit 81, unknown. Watermain replacement program phase 2 identified in capital plan; 2.4 km of AC main replacement with road restoration.
- Exampleville DA-2026-0102 at 200 Sample Avenue: fit 78, unknown. Drainage upgrade and detention pond construction for commercial site; includes culvert replacement and storm sewer extension.
- Testburg PL-2026-0302 at 600 Mock Crescent: fit 74, unknown. Municipal roadworks: intersection improvements, curb and gutter, sidewalk and bike lane construction on Demo Street corridor.
- Sampleton DP-2026-0201 at 300 Test Boulevard: fit 72, unknown. Park civil works: sports field regrading, pathway construction, site drainage and irrigation servicing.
8. These rezonings and development permits are early civil signals: excavation, underground utilities, site servicing, roads, drainage, curbs, sidewalks, and related contracts may appear 6-36 months before tender.
9. Tender-to-lead cross-link result:
- No tender-to-lead cross-link met the conservative municipality + address/keyword overlap threshold in this live run.
10. The printable Top 50 tab gives a screenshot-ready handout for management review.
11. The Outreach_Tracker turns leads into action: 6 rows tracked, with manual status and notes preserved across rebuilds by lead_id.

## ANALYZED AND SET ASIDE

12. TENDER_FINDER did not throw away the noise: 5 records were collected, scored, filtered, and retained for future reference.
13. This matters because Vancouver permits and context sources can be rescored later as the civil keyword model improves or when a known owner/developer becomes a target.

## SOURCE GROWTH ROADMAP

14. TENDER_FINDER includes a ranked source expansion roadmap - the "where does more volume come from next" answer. The Source_Roadmap_Printable tab (right after the Executive Summary) shows the one-page version; the Potential_Sources_Next tab ranks all 351 known candidate sources (351 potential/unaccounted, 0 flagged priority-next) by tender value, public access, and effort.
15. Be explicit with the audience: this is NOT fake pipeline volume. It is a prioritized worklist of data sources to verify, connect, or monitor - paid and login-gated sources are marked honestly as manual, email-alert, relationship, or paid-decision paths, never scraped.

## NEXT STEP

16. The Action_Center tab tells the user exactly where direct public connectors are active, where browser-review evidence exists, and where email alerts remain the compliant parallel channel, with no credential storage in TENDER_FINDER.
17. Email Alert Intake is available in this runtime package. Register on portals and enable civil alerts to activate more live tender coverage.
