# Getting Started with Tender Finder

Tender Finder is an internal weekly beta for Windows. A non-technical operator
can launch it by double-clicking `Launch_TENDER_FINDER_GUI.bat`; no console-only
workaround is required.

## First launch

The launcher checks for Python 3.11+, creates `.venv`, installs
`requirements.txt`, installs Playwright Chromium, verifies runtime imports, and
then opens the GUI. If a step fails, the setup window shows an actionable error
and returns non-zero. Setup never replaces the canonical repository-relative
launcher with an absolute-path copy.

The clean ZIP deliberately has no virtual environment, so first-run internet
access is expected. An optional Desktop shortcut points to the canonical
launcher. If shortcut creation is unavailable, double-click the launcher in the
program folder.

## Run tab

- **Live Run** contacts enabled, runtime-eligible public sources. It never logs
  in, stores portal credentials, bypasses a browser check, or solves a CAPTCHA.
- **Offline/Test Run** reads packaged/local inputs with `--no-fetch`.
- **Run Self-Test** uses the same authoritative offline runner as
  `verify_package.bat` and shows separate PASS/FAIL/SKIP/excluded/no-fixture
  totals.

The output path and resulting manifest/workbook paths remain visible. Stop
terminates the process tree and marks partial output; Pause stops at a safe
stage boundary; Resume recomputes into the same output folder rather than
pretending an unsafe mid-stage continuation occurred. Closing during a run
requires confirmation and stops child processes cleanly.

## Keywords tab

Use **Open Keywords Workbook**, save edits in `config\keywords.xlsx`, then
select **Validate Keywords** and **Reload Keywords**. The tab shows canonical
and effective paths, validation time, active/inactive counts, categories,
errors, and external last-known-good status.

`RESCORE_ALWAYS` means current effective rules govern current score, tier,
gate, label, and bucket. Check `Keyword_Change_Audit` for visible old/new
changes. Manual `Status`, `Notes`, `Assigned To`, and Weekly Review Log data are
preserved by stable ID.

## Source Checks

The table comes from `config\sources.csv` and displays operational status and
last test metadata. Configuration validation, offline parser testing, and
explicit one-source live testing are separate actions. A missing fixture is
reported as not tested, not PASS; only a structured live test can assign
`verified_live`.

## Runtime locations

Normal outputs and mutable state are outside the program folder beneath
`C:\tenderfinder_out` (or an explicitly selected external output root). This
includes run history, logs/manifests, email state, registry backups, keyword
validation/LKG state, browser state, screenshots, and Self-Test artifacts.

The editable source configuration files remain in `config\`; keep ordinary
backups before large manual edits.
