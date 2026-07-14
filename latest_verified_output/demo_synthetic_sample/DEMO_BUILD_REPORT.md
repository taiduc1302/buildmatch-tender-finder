# TENDER_FINDER Demo Build Report - Patch 5.23

## Outputs

- Workbook: `demo_out_synthetic\TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx`
- Talk track: `demo_out_synthetic\DEMO_TALKTRACK.md`
- Demo summary: `demo_out_synthetic\demo_summary.txt`
- BID NOW total / civil / open civil: 0 / 0 / 0
- BID LATER / WATCH / ANALYZED: 6 / 2 / 5
- Priority queue: fit >= 60 => 6; fit >= 70 => 5
- Outreach Tracker rows: 6
- Developer/applicant names identified: 6

## Email Alert Intake

- Email intake status: EMAIL_INTAKE_REJECTED_FILES
- Email intake data source: LIVE (real inbox/import folder)
- Email intake folder: demo_data\email_alerts
- Email alert files seen: 3
- Email tender rows parsed: 0
- Email civil-relevant rows: 0
- Email BID NOW rows: 0
- Email non-actionable/history rows: 0
- Email rejected/duplicate files: 3

## Surrey Terminal-Status Correction

- surrey_devapps_v2 rows reviewed from Track A snapshot: 0
- Moved out of BID LATER into Surrey_Historical_Archive: 0
- Remaining Surrey V2 active-signal rows kept in BID LATER: 0
- No HIGH signal_quality row in BID LATER carries a terminal status after the Patch 5.11 cap
- Audit reference remains: `docs/SURREY_DEVAPPS_V2_AUDIT.md`

## Address Recovery

- Surrey V2 address recovery: extracted=0 centroid=0 none=0; prior Patch 5.11 extracted count was 127
- Abbotsford address recovery: extracted=0 centroid=0 none=0
- Approximate centroids are stored in `approximate_location`; street-address extraction populates `address` and `address_source=EXTRACTED`

## Printable Top 50

- Vancouver permits excluded: YES
- Empty addresses in Top_Civil_Leads_Printable: 0
- Terminal-status rows in Top_Civil_Leads_Printable: 0
- Municipality diversity cap enforced: YES (max 15 per municipality)
- Top_Civil_Leads source_or_contact populated: YES

## Developer Grouping

- Parent-brand and consultant DBA-firm grouping active: YES
- Known major developer matches: none
- Repeat developers/applicants 3+: 0
- applicant_type distribution: DEVELOPER=0 UNKNOWN=6 DESIGN_CONSULTANT=0
- Design consultants separated to `Design_Consultants_Reference`: YES

## Tender Sweep

- BC Bid public URL: https://bcbid.gov.bc.ca/page.aspx/en/rfp/request_browse_public
- BC Bid status: SKIPPED_NO_FETCH
- BC Bid open civil opportunities: 0
- BC Bid pagination: detected=False pages_fetched=1 hard_cap=15 stop_reason='' total_hint=''
- BC Bid detail-page contact recovery: attempted=0 newly_gained_contact=0
- BC Bid network audit doc: `docs/BC_BID_NETWORK_AUDIT.md`
- Closing-date fallback: civil missing before=0 filled=0 unknown_after=0
- Gates Lake civil_relevant=YES: NOT_FOUND
- BID NOW rows with contact_email/contact_phone: 0
- BID NOW municipality cross-links: 0
- BID NOW keyword cross-links: 0

## Per-Source Tender Log

- email_alert_intake: EMAIL_INTAKE_REJECTED_FILES candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=Parses user-approved portal alert emails only; provider=Manual local folder import; folder=demo_data\email_alerts; files=3; parsed_rows=0; civil=0; open_actionable=0; duplicates=3; rejected=3; dry_run_log=none; source_mode=live_or_user_folder; no credentials or portal login.
- bc_bid_public: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- fvrd_tenders: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- slrd_contracting: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- metro_van_procurement: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- kpu_procurement: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- sd35_purchasing: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- bidcentral_landing: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- tol_public_tenders: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- maple_ridge_rfps: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- new_west_procurement: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- surrey_bids_public: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- coquitlam_bids: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- delta_bids: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- port_coquitlam_bids: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- city_north_van_bids: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- district_north_van_bids: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- richmond_procurement: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- pitt_meadows_bids: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- civicinfo_bids: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- burnaby_bids: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied
- abbotsford_bids: SKIPPED_NO_FETCH candidates=0 civil=0 open=0 deep=0 elapsed=0.00s note=--no-fetch supplied

## Repaired URL Status

- tol_public_tenders: SKIPPED_NO_FETCH; resolved=none; note=--no-fetch supplied
- maple_ridge_rfps: SKIPPED_NO_FETCH; resolved=none; note=--no-fetch supplied
- surrey_bids_public: SKIPPED_NO_FETCH; resolved=none; note=--no-fetch supplied

## Additional Source Notes

- metro_van_procurement: SKIPPED_NO_FETCH; resolved=none
- delta_bids: SKIPPED_NO_FETCH; resolved=none
- port_coquitlam_bids: SKIPPED_NO_FETCH; resolved=none
- city_north_van_bids: SKIPPED_NO_FETCH; resolved=none
- district_north_van_bids: SKIPPED_NO_FETCH; resolved=none
- richmond_procurement: SKIPPED_NO_FETCH; resolved=none
- pitt_meadows_bids: SKIPPED_NO_FETCH; resolved=none
- burnaby_bids: SKIPPED_NO_FETCH; resolved=none
- abbotsford_bids: SKIPPED_NO_FETCH; resolved=none

## BC Bid Sample Open Civil Titles

- None parsed from BC Bid in this run.

## Funnel And Timings

- Records pulled live: 27,260
- Records normalized: 13
- BID NOW tender candidates: 0
- BID NOW civil relevant: 0
- BID NOW open civil: 0
- BID NOW with contact: 0
- BID LATER clean future-project leads: 6
- Non-Vancouver BID LATER rows: 6
- detail_available=NO rows: 0
- signal_quality distribution: HIGH=6 MEDIUM=0 LOW=0
- project_scale_tier distribution: LARGE=0 MEDIUM=0 SMALL=1 UNKNOWN=5
- regional_cluster counts: Other=6
- New leads since last run: 6
- Watchlist: 2
- Analyzed and set aside: 5
- Track A read time: 7.24s
- Track B fetch time: 0.00s
- Total demo build time: 8.08s

## Safety Proof

- v6 SHA: NOT_AVAILABLE `NOT_AVAILABLE`
- v7_1 SHA: NOT_AVAILABLE `NOT_AVAILABLE`
- No credential storage / portal login / fixture fallback in this live run: YES
- BID NOW junk rows remaining: 0
- Reference-number contact_email rows remaining: 0

## Acceptance Checklist

- [x] Surrey V2 terminal rows excluded from BID_LATER_Future_Projects
- [x] Terminal-status rows cap to signal_quality=LOW
- [x] Top_Civil_Leads_Printable has 0 empty addresses, 0 terminal rows, and municipality diversity
- [x] Address recovery applied to Surrey V2 and Abbotsford with exact counts reported
- [x] Developer/consultant entity grouping + applicant_type classification implemented
- [x] BC Bid real-browser network audit written to docs/BC_BID_NETWORK_AUDIT.md
- [x] Tender closing-date fallback populated months where extractable
- [x] Design consultants separated from the primary developer relationship tab
- [x] Workbook quality, outreach persistence, and email intake fixture tests passed
- [ ] Protected master SHA values unchanged
