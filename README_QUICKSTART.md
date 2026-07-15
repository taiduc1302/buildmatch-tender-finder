# TENDER_FINDER Quickstart

## Start by double-clicking

Double-click `Launch_TENDER_FINDER_GUI.bat`. On the first launch it creates a
private `.venv`, installs the required packages, and then opens the GUI. Later
launches open the GUI directly with `pythonw.exe` and do not leave a console
window open.

All generated workbooks, logs, manifests, settings, and run history are stored
under `C:\tenderfinder_out`; normal runs do not write runtime state into this
repository.

## First safe run

1. On **Run TENDER_FINDER**, click **Validate keywords**.
2. Click **Run Self-Test**. It is strictly offline and reports honest counts
   for passed, failed, skipped, and intentionally excluded checks.
3. After Self-Test shows `PASS`, click **Offline/Test Run** to rebuild from
   packaged/local inputs without contacting public sites.
4. Use **Open Workbook** or **Open Output Folder** when the run finishes.

Use **Live Run** only when you intend to contact the enabled public sources.
It never logs into a portal or bypasses a CAPTCHA. BC Bid may require a manual
browser check.

## Edit scoring rules

Open `config\keywords.xlsx`, edit the `Keywords` sheet, save it, return to the
GUI, and click **Validate keywords** before running. You can add rows, change a
weight, set `active` to `N`, or use `contains`, `exact`, or bounded `regex`
matching. Invalid rows stop the run with a sheet/row-specific message.

TENDER_FINDER uses `RESCORE_ALWAYS`: every run recomputes scores, gates,
labels, Vancouver signals where source data permits, tiers, and downstream
routing from the current workbook. The `Keyword_Change_Audit` sheet shows
stable-ID old/new score, tier, and bucket changes. Manual `Assigned To`,
`Status`, `Notes`, and the Weekly Review Log survive rescoring.

## Manage sources

Open **Source Checks**. The table is backed by the one canonical registry,
`config\sources.csv`.

- **Add Source** creates a disabled draft.
- **Edit Source** validates and saves atomically.
- **Enable / Disable** controls whether a source participates in a run.
- **Validate Registry** checks the entire file.
- **Test Selected Offline** validates configuration or parses a configured
  local fixture without network access.
- **Test Selected Live** contacts only the selected public source after an
  explicit confirmation.

Built-in adapters are selectable in the editor. An unsupported website can be
saved as a disabled `custom` draft, but it needs a code adapter before it can
be enabled.

## Manual email alerts

In **Email Alert Intake**, click **Create / Open Email Import Folder**, copy
approved `.eml` files into the folder, and click **Test Email Import**. When
the dry-run counts look right, click **Run With Email Alerts**. You can instead
select an existing local or OneDrive folder; TENDER_FINDER never needs mailbox
passwords and does not move or delete the source messages.
