# TENDER_FINDER Tender Intelligence - Final Product Handoff (Patch 5.20)

This is the one document to read before demoing or distributing TENDER_FINDER.

## What to open first

**Windows** - unzip `TENDER_FINDER_Handoff_Package.zip` (or use the
`TENDER_FINDER_Handoff_Package` folder), then:
1. Double-click `setup_tenderfinder_environment.bat` (once per computer).
2. Double-click `Launch_TENDER_FINDER_GUI.bat` (or the Desktop shortcut setup
   creates) every time after that.

**macOS** - unzip `TENDER_FINDER_Handoff_Package_macOS.zip` (or use the
`TENDER_FINDER_Handoff_Package_macOS` folder), then:
1. Double-click `setup_tenderfinder_environment.command` (once per Mac).
   If macOS refuses to open it, right-click > Open, or run
   `chmod +x *.command` in Terminal in that folder first.
2. Double-click `Launch_TENDER_FINDER_GUI.command` every time after that.

Both packages include `START_HERE(.md/_MAC.md)` (step-by-step) and
`FILES_EXPLAINED(.md/_MAC.md)` (what every file does).

## Where the output goes

The GUI writes each run to a timestamped folder under `C:\tenderfinder_out\`
(Windows) or `~/tenderfinder_out/` (macOS) - the exact path is shown in the
Last Run Result panel, with **Open Output Folder** and **Open Results
Workbook** buttons. Each run produces:

- `TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx` - the results workbook
- `demo_summary.txt` - plain-text headline summary
- `DEMO_TALKTRACK.md` - a ready-to-speak demo narrative
- `DEMO_BUILD_REPORT.md` - the technical build record

## What the VP should look at first (workbook tab order)

1. **Executive_Summary** - headline numbers and how to read the rest.
2. **Source_Roadmap_Printable** - deliberately the second tab: the
   one-page "Where TENDER_FINDER can grow next" roadmap (see below).
3. **Top_Civil_Leads_Printable** - top 50 leads with contacts.
4. **BID_NOW_Active_Tenders** - live public tender signals this run.
5. **BID_LATER_Future_Projects** - 7,537 future civil project leads
   (start at fit score >= 60).
6. **Analyzed_Set_Aside / Watchlist_Monitor** - proof TENDER_FINDER keeps and
   scores everything instead of throwing data away (25,119 analyzed,
   973 on watch).

## The source expansion roadmap

`Source_Roadmap_Printable` answers "where does more volume come from
next": 372 candidate sources ranked by tender value, public access,
and effort; top 25 recommended next; category and access breakdowns;
and recommended next patch priorities. Full detail (all 372 rows,
filterable) is in `Potential_Sources_Next`.

**Say this plainly in the demo: it is NOT lead volume.** It is a
ranked worklist of *data sources* to verify, connect, or monitor.
Paid and login-gated sources are marked honestly as manual,
email-alert, relationship, or paid-decision paths - TENDER_FINDER never
scrapes them.

## BC Bid browser check - what happens and why

BC Bid's public site sometimes puts an automated browser-check page in
front of its Opportunities list. When that happens TENDER_FINDER:

1. Opens a **visible** browser window to the public page (no login,
   no stored cookies, no CAPTCHA bypass - ever).
2. Waits up to **5 minutes** for a person to let the page load,
   showing an "action needed" message and a **Continue After Browser
   Check** button in the GUI. Click it once the page has loaded and
   TENDER_FINDER re-checks immediately.
3. If the page loads: parses the public listing and continues.
4. If not completed in time: reports status
   `BC_BID_USER_CHECK_NOT_COMPLETED` - explicitly "BC Bid was not
   read this run", never a fake zero or fake success.

Temporary browser state is deleted after every run.

## Run controls

- **Stop** - kills the build and any browser it opened; output so far
  stays on disk, marked partial (`PARTIAL_OUTPUT_README.txt` +
  `tenderfinder_stage_progress.json` show how far it got).
- **Pause** - stops at the next safe stage boundary (never mid-write)
  and records `tenderfinder_checkpoint.json`.
- **Resume** - honest behavior: the pipeline recomputes from inputs,
  so Resume restarts the build from the beginning into the same
  folder, and the GUI says so instead of pretending to skip ahead.

## The reviewed-leads workbook (Track A data)

Both packages ship `inputs\all_live_review.xlsx` (the Track A source
data), so a fresh unzip works immediately. Lookup order if it moves:
`TENDER_FINDER_REVIEW_XLSX` env var > saved `tenderfinder_runtime_config.json` >
package-local `inputs\` > legacy `C:\tenderfinder_out\patch5_10_live\` path.
If none exist, the GUI explains and opens a Browse dialog, then
remembers the choice. See `inputs\README_MISSING_REVIEW_WORKBOOK.md`.

## Test results (this release, all verified on a real run)

- Fresh product build: **Track A = 7,537 / 973 / 25,119** (BID LATER /
  Watchlist / Analyzed) - unchanged, exact.
- `Source_Roadmap_Printable` present as tab 2; `Potential_Sources_Next`
  holds all **372** ranked source rows.
- Fresh-unzip smoke test: extracted `TENDER_FINDER_Handoff_Package.zip` to a
  clean folder; discovery found the package-local workbook; a full
  fast-mode build ran from the extraction with exact Track A counts.
- Unit/integration suites: GUI launcher 16/16, source backlog 13/13,
  BC Bid status UX 9/9, macOS package scripts 8/8, Stop/Pause/Resume
  5/5 (including a real engine pause at a checkpoint), review-xlsx
  consistency 4/4, Surrey status parser 4/4, mirror-name PASS.
- Protected master workbooks (v6, v7_1): SHA-256 hashes verified
  unchanged.
- Package audit: no `.venv`, `__pycache__`, `.git`, secrets, cookies,
  tokens, or saved config in either package.

## Package paths

- Windows folder: `TENDER_FINDER_Handoff_Package\`
- Windows zip: `TENDER_FINDER_Handoff_Package.zip` (~5 MB)
- macOS folder: `TENDER_FINDER_Handoff_Package_macOS\`
- macOS zip: `TENDER_FINDER_Handoff_Package_macOS.zip` (~5 MB)

Superseded artifacts still at repo root (kept, not current):
`TENDER_FINDER_Handoff_Package_Final.zip`, `TENDER_FINDER_CLEAN_RUNTIME_PACKAGE\` -
use the two zips above.

## Remaining limitations (stated honestly)

- BID NOW volume depends on public pages; dense live tender volume
  still comes from enabling portal email alerts (see the workbook's
  `Email_Setup_Guide` tab). TENDER_FINDER does not log into portals.
- BC Bid requires a human for its browser check when it appears; TENDER_FINDER
  guides the user through it but cannot (and will not) automate it.
- Resume after Pause restarts the build rather than skipping ahead -
  the pipeline recomputes from inputs by design.
- The macOS package is script-verified (bash syntax, LF endings, no
  Windows paths, path-discovery tests) but has not been executed on
  physical Apple hardware; do one smoke run on a real Mac before
  handing it out.
- Zip archives cannot carry the macOS execute bit; the docs and setup
  script cover this (`chmod +x *.command` / right-click Open).
