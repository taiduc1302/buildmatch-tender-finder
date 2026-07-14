# TENDER_FINDER Tender Intelligence - Start Here (macOS)

This folder is everything you need to run TENDER_FINDER on a Mac.
No programming knowledge required. Follow the steps in order.

## Step 1: One-time setup

1. Double-click **`setup_tenderfinder_environment.command`**.
   - If macOS says the file is from an "unidentified developer,"
     right-click (or Control-click) it and choose **Open**, then Open
     again in the dialog. If the files won't run at all, open Terminal
     in this folder and run: `chmod +x *.command`
2. A Terminal window opens and does the following automatically:
   - Checks that Python 3 is installed. If it isn't, it prints a
     download link (python.org is recommended because its installer
     includes the Tk window toolkit TENDER_FINDER's GUI needs).
   - Creates a private Python environment (`.venv`) just for TENDER_FINDER.
   - Installs the small number of packages TENDER_FINDER needs.
   - Downloads the small browser component TENDER_FINDER uses to read BC Bid
     tender listings (a few hundred MB, only happens once).
3. When you see "Setup complete", press Return to close the window.

This takes 5-10 minutes depending on internet speed. You only do this
once per Mac.

## Step 2: Every time after that - just run it

Double-click **`Launch_TENDER_FINDER_GUI.command`**.

A window opens with three things to check:

1. **Run Mode** - leave on "Full Live Sweep" for a normal run. Only
   pick "Fast Mode" to re-check existing leads without waiting for
   live tender sites (useful on slow internet).
2. **Output Folder** - where TENDER_FINDER saves results. The default (a
   `tenderfinder_out` folder in your home folder) is fine for most people.
3. **Run TENDER_FINDER Sweep** - click this to start.

The Current Step area and color-coded build log show progress. When
the build finishes, the Last Run Result panel shows the headline
numbers, and two buttons unlock:

- **Open Output Folder** - opens the folder with all result files.
- **Open Results Workbook** - opens the results spreadsheet directly.

While a build runs you can also use:

- **Stop** - terminates the build and any browser window it opened;
  output produced so far stays on disk, clearly marked as partial.
- **Pause** - TENDER_FINDER finishes its current stage (never cutting a file
  off mid-write), then stops at a safe checkpoint. **Resume**
  continues after a pause; honest note: stages before the workbook
  can't skip ahead safely, so Resume restarts the build from the
  beginning into the same folder.
- **Continue After Browser Check** - if BC Bid shows its browser-check
  page, TENDER_FINDER opens a visible browser window and waits up to 5 minutes
  for you to let the page load (completing any CAPTCHA yourself).
  Click this button once the page has loaded and TENDER_FINDER re-checks
  immediately. If the check isn't completed in time, the run reports
  it honestly instead of pretending BC Bid had nothing.

If the summary says BC Bid was "temporarily blocked by the site's
bot-check," or that it "needs a person to clear a quick check," that
is a normal, occasional thing with a live government site - not a
TENDER_FINDER problem. Every other tender source in that run is unaffected.
TENDER_FINDER never logs into portals, never stores passwords, and never
solves CAPTCHAs for you.

## Command-line alternative (no GUI)

- **`run_tenderfinder_demo.command`** - full live sweep
- **`run_tenderfinder_demo_fast.command`** - fast mode (skips live fetching)

Both print progress to a Terminal window and open the results when
done.

## The reviewed-leads workbook (Track A data)

TENDER_FINDER builds its Track A counts (BID LATER / Watchlist / Analyzed)
from a reviewed-leads workbook, `all_live_review.xlsx`. TENDER_FINDER looks
for it in this order:

1. the `TENDER_FINDER_REVIEW_XLSX` environment variable (if set),
2. a path you previously picked (saved in `tenderfinder_runtime_config.json`
   in this folder),
3. **`inputs/all_live_review.xlsx` in this package** - if the file
   shipped with your copy of the package, everything just works,
4. the legacy path `~/tenderfinder_out/patch5_10_live/all_live_review.xlsx`.

If none of those exist, the GUI explains what it needs and opens a
Browse dialog so you can point at the file - your choice is remembered
for future runs. See `inputs/README_MISSING_REVIEW_WORKBOOK.md` for
details. If the file is genuinely missing, TENDER_FINDER tells you plainly -
it never fails silently or invents numbers.

## Source Growth Roadmap (new)

The results workbook now leads with the source expansion story:

- **`Source_Roadmap_Printable`** - the tab right after
  `Executive_Summary`: a one-page, business-readable roadmap ("Where
  TENDER_FINDER can grow next") with the universe counts, the top 25
  recommended next sources, category and access breakdowns, and
  recommended next patch priorities.
- **`Potential_Sources_Next`** - the full detail: every candidate
  source, ranked and filterable.

To be clear about what this is:

- It is **not** fake pipeline volume, leads, or tenders. It is a
  prioritized to-do list of *data sources*.
- Public, active-tender sources that could produce BID NOW results
  rank highest; paid or login-gated sources are marked honestly as
  manual, email-alert, relationship, or paid-decision paths - TENDER_FINDER
  never scrapes them.

What the category codes on that tab mean, in plain English:

| Category | Meaning |
|---|---|
| `A_active_tender` | Active tender portals - open bid opportunities you could respond to now |
| `B_dev_applications` | Development applications - rezoning/subdivision/servicing filings that become civil work later |
| `C_council_agendas` | Council agendas and minutes - early approval and capital-award signals |
| `D_capital_future_infrastructure` | Capital plans and future infrastructure - budgeted projects before they go to tender |
| `E_paid_intelligence` | Paid intelligence services - subscription products; a business decision, never scraped |
| `F_gc_developer_invites` | General contractor / developer invite networks - sub-trade opportunities via relationships |
| `G_news_early_signal` | News and announcements - earliest but least structured project signals |
| `I_first_nations_indigenous_infrastructure` | First Nations and Indigenous infrastructure - community and partnership-driven projects |
| `K_private_developer_pipeline` | Private developer pipelines - land assembly and servicing signals before public filings |

## What's in this folder

See **`FILES_EXPLAINED_MAC.md`** for a plain-English description of
every file in this package.
