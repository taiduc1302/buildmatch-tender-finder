# PATCH 4.3 FINAL REPORT - Tavily Writer Hotfix + Cleaned URLs

## Summary
Patch 4.3 starts from `TENDER_FINDER_bulk_harvest_patch_attempt_4_2_source_register_expanded.zip` and adds a targeted hotfix for the link-checker output writer, preserves all Tavily replacement candidates, and creates a cleaned copied workbook:

`00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7_1_cleaned_urls.xlsx`

This patch does **not** overwrite protected v6 and does **not** overwrite the v7 source-expanded workbook. The final package excludes the local `.env.tenderfinder.local` secret file so API keys are not committed.

## Inputs used
- Base package: `TENDER_FINDER_bulk_harvest_patch_attempt_4_2_source_register_expanded.zip`
- Protected workbook: `00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx`
- Source-expanded workbook: `00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7_source_expanded.xlsx`
- Candidate source used: `01 Code/CONNECTOR_SWEEP/link_audit_out_v7_tavily/TENDER_FINDER_Source_Register_URL_Live_Audit.csv`
- Previous Tavily audit/fix outputs under: `01 Code/CONNECTOR_SWEEP/link_audit_out_v7_tavily/`

## Workbooks created
- Created: `00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7_1_cleaned_urls.xlsx`
- Source_Register row count: **159**
- `URL / Portal` remains present and active: **True**
- Dirty URL strings found after cleanup: **0**
- Added workbook sheet: `Replacement_Candidate_Review`

## Protected workbook checks
- v6 hash unchanged: **ca20abca726a31828a2b6033bd8d44a1b4b94b301854bcf0d0c80afd4e54bc7c**
- v7 source-expanded hash unchanged: **c9462052d6f4811c7ee915e1557b30f987dad7079f5b8a1e92b39468ea7db657**
- v7_1 cleaned workbook hash: **a1dd67e0c62473b1ce9f5e46a8f8a3faff3a866e716bb96c33c848d217941f3d**
- Protected v6 was not overwritten.
- Original v7 source-expanded workbook was not overwritten.

## Replacement candidate preservation summary
- Candidate rows preserved in `06 QA/TENDER_FINDER_Tavily_Replacement_Candidates_Review.csv`: **27**
- ACCEPT candidates applied: **10**
- ACCEPT_REVIEW candidates applied: **2**
- REVIEW candidates preserved: **1**
- REJECT candidates preserved: **12**
- Rejected candidates not applied: **12**

`REJECT` was treated as “do not apply automatically,” not “delete.” Rejected and review candidates are preserved for future manual review and future scoring improvement.

## Applied replacements
|source_id|source_name|old_url|candidate_url|review_decision|review_reason|
|---|---|---|---|---|---|
|SRC-058|Infrastructure Canada / Public Transit Fund|https://canada.ca|https://housing-infrastructure.canada.ca/cptf-ftcc/index-eng.html|ACCEPT|Official Government of Canada infrastructure fund page; specific and more useful than generic canada.ca.|
|SRC-083|KPU Procurement Services / current opportunities|https://www.kpu.ca/procurement/current-opportunities|https://www.kpu.ca/procurement/Vendor-Help|ACCEPT|Official KPU procurement/vendor page on same domain; stable procurement pathway.|
|SRC-084|Langley School District purchasing and tenders|https://www.sd35.bc.ca/board-of-education/administration/purchasing-tenders|https://www.sd35.bc.ca/purchasing-logistics|ACCEPT|Official Langley SD purchasing/logistics page on same domain.|
|SRC-090|City of Langley Capital Projects|https://www.langleycity.ca/city-services/engineering/capital-projects|https://www.langleycity.ca/business-development/capital-projects|ACCEPT|Official City of Langley capital projects page on same domain.|
|SRC-094|Pitt Meadows Capital Projects|https://www.pittmeadows.ca/engineering/capital-projects|https://www.pittmeadows.ca/city-services/transportation-infrastructure|ACCEPT_REVIEW|Official Pitt Meadows infrastructure page and likely more stable than broken capital-projects path; applied as clearly official owner page.|
|SRC-097|Township of Langley Capital Projects|https://www.tol.ca/en/engineering/capital-projects.aspx|https://www.tol.ca/en/building-development/capital-projects.aspx|ACCEPT|Official Township of Langley capital projects page on same domain.|
|SRC-102|FortisBC Major Projects / Capital Pipeline|https://www.fortisbc.com/about-us/major-projects|https://www.fortisbc.com/about-us/projects-planning|ACCEPT_REVIEW|Official FortisBC projects/planning page; broader but clearly official and safer than broken major-projects path.|
|SRC-142|Abbotsford Bids & Tenders endpoint|https://www.abbotsford.ca/business/bids-tenders|https://www.abbotsford.ca/city-hall/procurement-services|ACCEPT|Official City of Abbotsford procurement services page.|
|SRC-143|Burnaby Bidding Opportunities|https://www.burnaby.ca/doing-business/bidding-opportunities|https://www.burnaby.ca/business/doing-business-with-the-city/bid-opportunities|ACCEPT|Official City of Burnaby bid opportunities page.|
|SRC-148|District of North Vancouver Bids & Tenders endpoint|https://www.dnv.org/business/bids-and-tenders|https://www.dnv.org/business-development/bid-opportunities|ACCEPT|Official District of North Vancouver bid opportunities page.|
|SRC-154|Abbotsford School District doing business / tenders|https://www.abbyschools.ca/doing-business|https://finance.abbyschools.ca/purchasing/bid-opportunities/finance|ACCEPT|Official Abbotsford School District purchasing/bid opportunities page.|
|SRC-158|Delta School District tenders|https://www.deltasd.bc.ca/our-district/business/tenders|https://www.deltasd.bc.ca/district/business-opportunities|ACCEPT|Official Delta School District business opportunities page.|

## Rejected/unapplied candidates retained
|source_id|source_name|candidate_url|review_decision|review_reason|
|---|---|---|---|---|
|SRC-064|Business in Vancouver / Western Investor|https://www.biv.com/news/entertainment-media-sports/5-things-you-probably-didnt-know-were-founded-vancouver-8268017|REJECT|Random BIV article, not a stable procurement/source page.|
|SRC-091|Maple Ridge Capital Projects|https://www.mapleridge.ca/news/maple-ridge-moves-key-infrastructure-projects-forward-2026-2030-capital-plan|REJECT|News article/capital-plan story, not a stable capital projects source page.|
|SRC-095|Surrey Capital Construction Projects|https://www.surrey.ca/news-events/news/surrey-accelerates-delivery-of-major-capital-projects-across-city|REJECT|Surrey news article, not a stable capital project source page.|
|SRC-117|Adera Development Projects|https://adera.com/residential|ACCEPT_REVIEW|Official Adera page but too broad/generic to apply automatically.|
|SRC-118|Anthem Properties project news / portfolio|https://anthemproperties.com/anthem-and-bgo-to-develop-purpose-built-rental-community-in-coquitlam-centre|REJECT|One-off developer news/project article, not a stable portfolio/source page.|
|SRC-133|City of Langley Council Agendas|https://www.langleycity.ca/media/file/bylaw-3310-adp-reportdp-08-244505-200a-streetpdf|REJECT|Specific bylaw/report PDF, not stable council-agenda source.|
|SRC-134|Pitt Meadows Council Agendas|https://www.pittmeadows.ca/homes-development/zoning-land-use/zoning-rezoning|REVIEW|Official Pitt Meadows zoning/rezoning page but does not replace council-agenda workflow automatically.|
|SRC-141|Tsawwassen First Nation Doing Business with TFN|https://tsawwassenfirstnation.com/wp-content/uploads/2026/04/RFQ-for-Website.pdf|REJECT|One-off RFQ PDF, not stable TFN procurement/business source page.|
|SRC-149|Mission Bids & Tenders endpoint|https://www.missiontexas.us/257/Bid-Opportunities|REJECT|Mission Texas result for Mission BC; wrong jurisdiction.|
|SRC-150|New Westminster Bids & Tenders endpoint|https://www.newwestcity.ca/database/files/NWRFP_11_26_Commissioning_Authority_MUCF.pdf|REJECT|One-off RFP PDF, not stable New Westminster tenders/procurement page.|
|SRC-152|BC Ferries procurement / contract opportunities|https://www.bcferries.com/news-releases/bcferries-awards-contract-for-additional-salish-class-vessel|REJECT|BC Ferries news release, not procurement/contract opportunities page.|
|SRC-155|Burnaby School District tenders|https://burnabyschools.ca/wp-content/uploads/2022/11/NEW-3.80-Policy-Purchasing-Goods-and-Services.pdf|REJECT|Policy PDF, not active tender/procurement source page.|
|SRC-156|Chilliwack School District tenders|https://www.sd33.bc.ca|ACCEPT_REVIEW|Official SD33 homepage but too generic; preserve for manual review only.|
|SRC-157|Coquitlam SD43 tenders|https://www.sd43.bc.ca/Board/Policies/Administrative%20Procedures/AP%20514.pdf|REJECT|Administrative policy PDF, not tenders/procurement source page.|
|SRC-159|Providence Health Care Tenders & RFPs|https://thedailyscan.providencehealthcare.org/2019/05/bidding-process-launched-to-build-new-1-9-billion-st-pauls-hospital-new-sph|REJECT|Daily Scan/news article, not stable Providence tender/RFP source page.|

## Output writer hotfix details
Patched `tenderfinder_live_link_checker.py` only for output-writing safety. The hotfix adds:

- output directory creation with `parents=True, exist_ok=True`;
- same-directory temporary file writing;
- atomic `os.replace()` where possible;
- direct-write fallback if atomic replace fails;
- preservation of already written outputs during the same run;
- output-write error tracking through validation;
- replacement candidate output based on any non-empty `replacement_candidate_url`, not only status labels;
- `TENDER_FINDER_Source_Register_Replacement_Candidates.csv` always written, even when it contains only headers.

A synthetic writer test with one replacement candidate passed and created all required outputs, including a non-empty `TENDER_FINDER_Source_Register_Replacement_Candidates.csv`.

## Test commands run
From `0623 v4 Tender Finder Final/01 Code/CONNECTOR_SWEEP/`:

```bash
python -m py_compile tenderfinder_raw_sweep.py tenderfinder_master_io.py tenderfinder_bulk_io.py tenderfinder_link_preflight.py tenderfinder_live_link_checker.py tenderfinder_source_registry.py tenderfinder_guards.py
```
Result: **PASS**.

```bash
python tenderfinder_raw_sweep.py --help
python tenderfinder_live_link_checker.py --help
```
Result: **PASS**. Preflight options remain visible through `tenderfinder_raw_sweep.py`.

```bash
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7_1_cleaned_urls.xlsx" --preflight-links --preflight-no-search --preflight-output-dir "./link_audit_out_v7_1_no_search" --preflight-timeout 20 --preflight-retries 2 --preflight-workers 6
```
Result: **TIMEOUT in sandbox after 180 seconds**. The command started through `tenderfinder_raw_sweep.py`, read the v7_1 workbook successfully, found `Source_Register`, recognized `URL / Portal`, and began checking URLs. The sandbox run did not finish the live HTTP pass.

Fallback command run through `tenderfinder_raw_sweep.py`:

```bash
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7_1_cleaned_urls.xlsx" --preflight-links --preflight-no-search --preflight-output-dir "./link_audit_out_v7_1_no_search" --preflight-timeout 20 --preflight-retries 2 --preflight-workers 6 --dry-run
```
Result: **PASS**. It read v7_1, processed 159 source rows / 159 URL tasks in dry-run mode, and created all required outputs.

Tavily-search command status:

```bash
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7_1_cleaned_urls.xlsx" --preflight-links --preflight-search-provider tavily --preflight-output-dir "./link_audit_out_v7_1_tavily" --preflight-timeout 20 --preflight-retries 2 --preflight-workers 6
```
Result: **SKIPPED as a live Tavily search in the final package** because `.env.tenderfinder.local` is intentionally not committed. A dry-run through `tenderfinder_raw_sweep.py` was run instead:

```bash
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7_1_cleaned_urls.xlsx" --preflight-links --preflight-search-provider tavily --preflight-output-dir "./link_audit_out_v7_1_tavily" --preflight-timeout 20 --preflight-retries 2 --preflight-workers 6 --dry-run
```
Result: **PASS**. It created all required output files.

Synthetic writer hotfix test:

```bash
python - <<'PY'
# Imported tenderfinder_live_link_checker.write_outputs() and wrote a one-row synthetic
# replacement candidate to link_audit_out_writer_hotfix_test.
PY
```
Result: **PASS**. `replacement_rows=1`, output validation passed.

## Preflight results before/after
Before Patch 4.3, the available Tavily audit source had:
- URL audit rows: **159**
- Fix Queue rows: **46**
- Replacement candidate rows extracted/preserved: **27**

After Patch 4.3:
- v7_1 no-search dry-run audit rows: **159**
- v7_1 no-search dry-run Fix Queue rows: **12**
- v7_1 Tavily dry-run audit rows: **159**
- v7_1 Tavily dry-run Fix Queue rows: **12**

The live no-search run timed out in this sandbox, so the dry-run outputs prove integration/output generation but do not replace a local live-network preflight.

## Required output files created
### `link_audit_out_v7_1_no_search`
- `TENDER_FINDER_Source_Register_URL_Live_Audit.csv` - exists=True, size=70439, rows=159
- `TENDER_FINDER_Source_Register_URL_Live_Audit.xlsx` - exists=True, size=33120
- `TENDER_FINDER_Source_Register_Fix_Queue.csv` - exists=True, size=3304, rows=12
- `TENDER_FINDER_Source_Register_Replacement_Candidates.csv` - exists=True, size=602, rows=0
- `TENDER_FINDER_Source_Register_Cleaned_For_Script.csv` - exists=True, size=42662, rows=159
- `TENDER_FINDER_Link_Check_Run_Log.txt` - exists=True, size=3550
- `TENDER_FINDER_Link_Check_Debug_Log.txt` - exists=True, size=22267

### `link_audit_out_v7_1_tavily`
- `TENDER_FINDER_Source_Register_URL_Live_Audit.csv` - exists=True, size=70439, rows=159
- `TENDER_FINDER_Source_Register_URL_Live_Audit.xlsx` - exists=True, size=33120
- `TENDER_FINDER_Source_Register_Fix_Queue.csv` - exists=True, size=3304, rows=12
- `TENDER_FINDER_Source_Register_Replacement_Candidates.csv` - exists=True, size=602, rows=0
- `TENDER_FINDER_Source_Register_Cleaned_For_Script.csv` - exists=True, size=42662, rows=159
- `TENDER_FINDER_Link_Check_Run_Log.txt` - exists=True, size=3546
- `TENDER_FINDER_Link_Check_Debug_Log.txt` - exists=True, size=22249

### `link_audit_out_writer_hotfix_test`
- `TENDER_FINDER_Source_Register_URL_Live_Audit.csv` - exists=True, size=952, rows=1
- `TENDER_FINDER_Source_Register_URL_Live_Audit.xlsx` - exists=True, size=5698
- `TENDER_FINDER_Source_Register_Fix_Queue.csv` - exists=True, size=626, rows=1
- `TENDER_FINDER_Source_Register_Replacement_Candidates.csv` - exists=True, size=952, rows=1
- `TENDER_FINDER_Source_Register_Cleaned_For_Script.csv` - exists=True, size=513, rows=1
- `TENDER_FINDER_Link_Check_Run_Log.txt` - exists=True, size=3251
- `TENDER_FINDER_Link_Check_Debug_Log.txt` - exists=True, size=1143

## Remaining Fix Queue
- Remaining Fix Queue count from v7_1 no-search dry-run output: **12**
- This is a dry-run/sandbox count and should be rechecked with a local live HTTP run.

## Remaining connector/manual workflow counts
Counts based on v7_1 `Source_Register` routing fields:
- Rows requiring connector-type workflow: **5**
- Rows requiring manual/login/relationship workflow: **51**

## Known limitations
- Live no-search preflight did not complete in the sandbox; it timed out after starting successfully through `tenderfinder_raw_sweep.py`.
- Tavily live search was not run in the final packaged state because API keys are intentionally not committed.
- The preflight dry-runs prove workbook reading, URL-column support, writer behavior, output file creation, and runner integration, but they do not prove live HTTP status accuracy.
- Some accepted replacements are `ACCEPT_REVIEW` and were applied only when they were clearly official owner pages; these should still be manually checked before production use.
- `TENDER_FINDER_Source_Register_Replacement_Candidates.csv` can validly contain only headers when no search runs or when dry-run mode is used.

## Next recommended steps
1. On a local machine with network access, add a local `.env.tenderfinder.local` from `.env.tenderfinder.local.example` and run the Tavily-enabled preflight against v7_1.
2. Review `06 QA/TENDER_FINDER_Tavily_Replacement_Candidates_Review.csv`, especially ACCEPT_REVIEW rows.
3. Review the remaining Fix Queue and separate real broken URLs from manual/login/connector-only sources.
4. Only after local live preflight passes, decide whether to sync cleaned URLs back into the working Source Register path.
