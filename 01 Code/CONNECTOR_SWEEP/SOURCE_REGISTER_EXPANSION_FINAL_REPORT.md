# SOURCE_REGISTER_EXPANSION_FINAL_REPORT.md

## Patch
Patch 4.2 — Source Register Expansion Integration

## Base package
Base package used: `TENDER_FINDER_bulk_harvest_patch_attempt_4_1_TAVILY_KEY.zip`.

The protected v6 workbook was used only as the source workbook and was not overwritten.

## Workbook created
Created copied workbook:

`00 Master / TENDER_FINDER_Tender_Intelligence_Working_Master_v7_source_expanded.xlsx`

## Source expansion inputs used
Used the available expanded source-register file from the uploaded link-checker package:

- `TENDER_FINDER_Link_Checker_v2.1.0 / TENDER_FINDER_Source_Register_PreScript_Audit.xlsx`
- `TENDER_FINDER_Link_Checker_v2.1.0 / TENDER_FINDER_Source_Register_PreScript_Audit.csv`

Copies were preserved under:

`04 RESEARCH REFERENCE / SOURCE_REGISTER_EXPANSION /`

## Source_Register merge summary
- Old source count: 68
- New source count: 159
- Rows added: 91
- Duplicates skipped: 0
- Expansion candidates considered: 91
- Dirty old URL/portal values cleaned or moved to notes: 47
- Blank URL rows retained for real manual/review workflows: 12
- Dirty URL strings remaining in `URL / Portal`: 0

The v7 Source_Register keeps `URL / Portal` as the workbook URL column. Values in that column are either a single clean `http(s)` URL or blank for true manual/review sources. Dirty strings such as `vendor`, `municipal sites`, `https://data.burnaby.ca + BurnabyMap`, or multi-source URL cells were not left in the URL field.

## Routing summary
Every Source_Register row was classified into one of the approved routes:

- Active_Tenders: 51
- Future_Projects: 72
- Run_Queue: 13
- Bulk_Intake_Raw: 14
- Paid_Intelligence: 9
- Rejected_Archive: 0

## Connector/manual workflow summary
- Rows requiring connector or connector-style handling: 31
- Rows requiring manual workflow, login workflow, PDF/manual review, or relationship workflow: 54

Adding a source to `Source_Register` does not mean it has a coded connector. Rows are now supportable as simple HTML listings, RSS feeds, connector-required portals, manual/login workflows, development/capital pipelines, news/early-signal sources, or GC/relationship workflows.

## Preserved v6 sheets
The following v6 sheets are preserved in the new v7 workbook:

- README_START_HERE
- Dashboard
- Config_Scope
- Source_Register
- Municipal_Coverage
- Active_Tenders
- Future_Projects
- Run_Queue
- Rejected_Archive
- Weekly_Review_Log
- Priority_Monitoring
- Automation_Plan
- Phased_Rollout
- Paid_Intelligence
- Prompt_Pack
- Cleanup_Log
- Project_Plan
- Backup_Raw_Imported

Additional existing workbook sheets such as `Lists` and `Examples_Do_Not_Use` were also preserved.

## Preflight commands run
Attempted live integrated preflight through `tenderfinder_raw_sweep.py`:

```powershell
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7_source_expanded.xlsx" --preflight-links --preflight-no-search --preflight-output-dir "./link_audit_out_v7" --preflight-timeout 20 --preflight-retries 2 --preflight-workers 6
```

Result: PARTIAL / SANDBOX TIMEOUT. The command started through `tenderfinder_raw_sweep.py`, read the v7 workbook successfully, detected `Source_Register`, recognized the `URL / Portal` alias as `official_url`, loaded 159 rows, and began URL checks. The sandbox run timed out before completion.

Fallback integrated dry-run preflight through `tenderfinder_raw_sweep.py`:

```powershell
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7_source_expanded.xlsx" --preflight-links --preflight-no-search --preflight-output-dir "./link_audit_out_v7" --preflight-timeout 20 --preflight-retries 2 --preflight-workers 6 --dry-run
```

Result: PASS. The dry-run preflight read the real v7 workbook and created the required output files without opening, backing up, saving, or modifying the master workbook.

## Preflight result
- Preflight read v7 successfully: YES
- Integrated command ran through `tenderfinder_raw_sweep.py`: YES
- `URL / Portal` supported as URL alias: YES
- Source rows loaded by preflight: 159
- Extractable URLs reported by preflight: 147
- Fix Queue count: 12
- Replacement Candidates count: 0
- Cleaned For Script rows: 159
- Run Log created: YES
- Debug Log created: YES

The Fix Queue contains actual source rows requiring URL/manual review. No dummy placeholder rows were inserted.

## Output files created
- `link_audit_out_v7 / TENDER_FINDER_Link_Check_Debug_Log.txt` — size=21392
- `link_audit_out_v7 / TENDER_FINDER_Link_Check_Run_Log.txt` — size=3417
- `link_audit_out_v7 / TENDER_FINDER_Source_Register_Cleaned_For_Script.csv` — size=42566, rows=159
- `link_audit_out_v7 / TENDER_FINDER_Source_Register_Fix_Queue.csv` — size=3304, rows=12
- `link_audit_out_v7 / TENDER_FINDER_Source_Register_Replacement_Candidates.csv` — size=602, rows=0
- `link_audit_out_v7 / TENDER_FINDER_Source_Register_URL_Live_Audit.csv` — size=70150, rows=159
- `link_audit_out_v7 / TENDER_FINDER_Source_Register_URL_Live_Audit.xlsx` — size=33027


## Workbook protection check
- Protected v6 workbook hash before merge: `ca20abca726a31828a2b6033bd8d44a1b4b94b301854bcf0d0c80afd4e54bc7c`
- Protected v6 workbook hash after merge/preflight: `ca20abca726a31828a2b6033bd8d44a1b4b94b301854bcf0d0c80afd4e54bc7c`
- v6 unchanged: YES

The protected workbook `00 Master / TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx` was not overwritten.

## Known limitations
- The completed preflight output in this package is from integrated dry-run mode because the sandbox timed out during live HTTP checking.
- Live URL status should be rerun on a local/network-enabled machine if true HTTP status classification is required.
- The v7 workbook expands the Source_Register but does not create coded connectors for all new sources.
- Rows routed to manual/login/relationship workflows must not be scraped blindly.
- Sources with blank `URL / Portal` are intentional review/manual workflow items and should be resolved before simple scraping.
