# What Each File Does (macOS package)

A plain-English map of this handout package. Read `START_HERE_MAC.md`
first if you just want to run TENDER_FINDER - come back here if you want to
know what a specific file is for.

## Top-level files (double-click these)

| File | What it does |
|---|---|
| `setup_tenderfinder_environment.command` | Run this once. Creates TENDER_FINDER's private Python environment, installs packages, downloads the browser component. Right-click > Open the first time if macOS complains. |
| `Launch_TENDER_FINDER_GUI.command` | Opens the point-and-click TENDER_FINDER window. This is what you'll use every day. |
| `run_tenderfinder_demo.command` | Terminal (no-window-buttons) launcher for a full live sweep. Same underlying build as the GUI's "Full Live Sweep" mode. |
| `run_tenderfinder_demo_fast.command` | Terminal launcher for fast mode - rebuilds Track A (already-reviewed leads) and the intake plan without re-fetching live tender sites. Useful on slow internet. |

All four scripts find their own folder automatically (`cd "$(dirname
"$0")"`), so you can run them from anywhere. If they won't open, run
`chmod +x *.command` in Terminal once.

## `docs/` - reference material

| File | What it does |
|---|---|
| `GETTING_STARTED.md` | The original plain-English quick-start guide (written for Windows; the steps in START_HERE_MAC.md are the macOS equivalents). |
| `BC_BID_NETWORK_AUDIT.md` | Technical background on how TENDER_FINDER reads BC Bid's public tender listings, including why BC Bid occasionally shows a "temporarily blocked" or "needs a person to clear a check" status instead of results. TENDER_FINDER never logs into BC Bid, never stores a password, and never bypasses a CAPTCHA - if BC Bid's bot-check blocks it, TENDER_FINDER says so plainly instead of guessing or faking a result. |

## `01 Code/CONNECTOR_SWEEP/` - the program itself

| File | What it does |
|---|---|
| `tenderfinder_demo_three_buckets.py` | The core engine. Reads the already-reviewed leads workbook (Track A), optionally fetches live tender pages from municipal sites and BC Bid (Track B), sorts everything into three buckets (Bid Now / Bid Later / Watch), and writes the results workbook plus a plain-text summary and talk track. Both the GUI and the `.command` launchers run this file - it does the actual work. |
| `tenderfinder_launcher_gui.py` | The point-and-click window (built with Python's built-in Tkinter toolkit, one shared code path for Windows and macOS). It runs the engine as a background process and streams its progress into the color-coded log. Closing the window mid-build stops everything cleanly, including any browser window opened for BC Bid. |
| `tenderfinder_source_backlog.py` | Builds the Source_Roadmap_Printable and Potential_Sources_Next workbook tabs: loads the source-universe backlog from `data/`, scores and ranks every candidate source, and marks paid/login-gated sources honestly. A worklist of sources - never presented as leads. |
| `tenderfinder_review_workbook.py` | Finds the reviewed-leads workbook (Track A data) using the documented lookup order: `TENDER_FINDER_REVIEW_XLSX` env var, saved config, package-local `inputs/`, legacy home path. Also reads/writes `tenderfinder_runtime_config.json` when you pick the file in the GUI. |
| `tenderfinder_email_guidance.py` | Small helper that reports whether email-based lead intake is configured, partially configured, or off. |
| `tenderfinder_email_intake.py` | Handles the optional email-intake feature - pulling inbound lead-alert emails into the same review pipeline as web-sourced leads. |
| `requirements.txt` | The packages `pip` installs (openpyxl, beautifulsoup4, playwright). Setup installs these automatically. |
| `data/TENDER_FINDER_Source_Universe_Backlog_v2_EXPANDED.xlsx` | The source-universe backlog: 372 candidate sources across 6 sheets, including the Priority_Next_60 shortlist. Input data for the Potential_Sources_Next tab. |
| `data/TENDER_FINDER_Potential_Unaccounted_Sources_v2_EXPANDED.csv` | The 351 potential/unaccounted sources as a CSV - used to cross-check the XLSX and as a fallback if it is missing. |

## `inputs/` - Track A business data

| File | What it does |
|---|---|
| `inputs/all_live_review.xlsx` | The reviewed-leads workbook TENDER_FINDER builds Track A from (BID LATER / Watchlist / Analyzed). If present, every launcher and the GUI find it automatically. |
| `inputs/README_MISSING_REVIEW_WORKBOOK.md` | What to do if the workbook is not in this package - three plain-English recovery options. |

## What is deliberately NOT in this package

- **No `.venv` folder** - setup creates a fresh one per machine.
- **No test files** - the automated test suite lives in the
  development repository.
- **No master workbooks or proprietary lead data** - TENDER_FINDER's business
  data (the master tender list and the reviewed-leads workbook) is
  kept separate from source code on purpose. See "Before you run it
  on a NEW Mac" in `START_HERE_MAC.md`.
- **No signed `.app` bundle** - these are plain `.command` scripts by
  design; macOS may ask you to right-click > Open the first time.
- **No git history, secrets, cookies, or tokens.**
