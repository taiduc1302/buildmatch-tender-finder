# Getting Started with TENDER_FINDER Tender Intelligence

This is the plain-English version. If you can double-click a file on
Windows, you can run TENDER_FINDER.

## First time only: run setup

1. Find `setup_tenderfinder_environment.bat` in the main TENDER_FINDER folder.
2. Double-click it.
3. A black window opens and does the following for you, automatically:
   - Checks that Python is installed (if it isn't, it tells you exactly
     where to download it - see "If setup says Python is missing" below).
   - Creates a private Python environment just for TENDER_FINDER, so it can't
     conflict with anything else on your computer.
   - Installs the few extra packages TENDER_FINDER needs.
   - Downloads the small web browser TENDER_FINDER uses to read BC Bid tender
     listings. This step downloads a few hundred megabytes and can take
     a few minutes the first time - that's expected, and it only
     happens once.
   - Creates a **TENDER_FINDER Tender Intelligence** shortcut on your Desktop.
4. When you see "Setup complete", press any key to close the window.

This whole process typically takes 5-10 minutes depending on your
internet connection. You only need to do it once.

### If setup says Python is missing

The setup window will print a download link
(https://www.python.org/downloads/). Download and run that installer.
**On the very first screen of the Python installer**, check the box
labeled "Add python.exe to PATH" before clicking Install. Then run
`setup_tenderfinder_environment.bat` again.

### If no Desktop shortcut appears

Some computers don't allow shortcuts to be placed on the Desktop
automatically. If that happens, setup tells you so at the end and
points you to `Launch_TENDER_FINDER_GUI.bat` in the main TENDER_FINDER folder instead -
double-click that file any time you want to run TENDER_FINDER. It works exactly
the same as the Desktop shortcut.

## Every time after that: just run it

Double-click the **TENDER_FINDER Tender Intelligence** shortcut on your Desktop
(or `Launch_TENDER_FINDER_GUI.bat` in the TENDER_FINDER folder if you don't have the
Desktop shortcut).

A window opens with three things to check:

1. **Run Mode** - leave this on "Full Live Sweep" for a normal run. Only
   pick "Fast Mode" if you just want to re-check existing leads without
   waiting for live tender sites to load (useful on slow internet).
2. **Output Folder** - where TENDER_FINDER saves the results. The default is
   fine for most people; click "Browse..." if you want to choose a
   different folder.
3. **Run TENDER_FINDER Sweep** - click this to start.

While TENDER_FINDER runs, the Current Step area and color-coded log show what
it's doing. This takes a few minutes for a full sweep. When it
finishes, the Last Run Result panel shows the headline numbers, and
two buttons unlock:

- **Open Output Folder** - opens the folder with all the result files.
- **Open Results Workbook** - opens the results spreadsheet directly.

**Stop / Pause / Resume:** while a build runs you can click **Stop**
(terminates the build and any browser it opened; output produced so
far stays on disk, clearly marked as partial) or **Pause** (TENDER_FINDER
finishes its current stage - it never cuts a file off mid-write - then
stops at a safe checkpoint). **Resume** continues after a pause; to be
honest about it: stages before the workbook can't skip ahead safely,
so Resume restarts the build from the beginning into the same folder.

**If TENDER_FINDER can't find the reviewed-leads workbook** (for example, on a
new computer), it doesn't just fail - it explains what it needs, lets
you browse for the file, and remembers your choice for future runs.

If something goes wrong, TENDER_FINDER shows an error message explaining what
happened and tells you where the full error log was saved, instead of
just freezing or closing silently.

If you close the window while a build is still running, TENDER_FINDER asks you
to confirm first, then stops the build cleanly (including the small web
browser it may have opened for BC Bid) rather than leaving anything
running in the background.

**BC Bid browser check:** BC Bid sometimes shows an automated
browser-check page. When that happens, TENDER_FINDER opens a visible browser
window to BC Bid's public page and waits up to 5 minutes for you to
let it finish loading (completing any CAPTCHA yourself - TENDER_FINDER never
logs in or solves one for you). The GUI shows a clear "action needed"
message and a **Continue After Browser Check** button - click it once
the page has loaded and TENDER_FINDER re-checks immediately. If the check isn't
completed in time, the run reports it honestly ("BC Bid was not read
this run") instead of pretending BC Bid had nothing. Every other
tender source in that run is unaffected.

## Command-line alternative

If you prefer not to use the GUI, `run_tenderfinder_demo.bat` (full sweep) and
`run_tenderfinder_demo_fast.bat` (fast mode) in the main TENDER_FINDER folder do the same
thing without opening a window with buttons - just double-click and
watch the console output.
