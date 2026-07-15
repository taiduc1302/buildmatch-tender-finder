# Tender Finder Quickstart

## Start by double-clicking

Double-click `Launch_TENDER_FINDER_GUI.bat`. The first launch creates `.venv`,
installs dependencies and Playwright Chromium, then opens the GUI. This is a
clickable Python application, not a self-contained executable; first-run setup
needs Python 3.11+ and internet access.

All normal output and mutable state goes beneath `C:\tenderfinder_out` (or a
selected external output root), not into the program folder.

## First safe run

1. Open **Keywords** and click **Validate Keywords**.
2. Click **Run Self-Test** and require PASS with zero failed/no-fixture checks.
3. Click **Offline/Test Run** to rebuild only from packaged/local inputs.
4. Open the workbook and inspect `Keyword_Change_Audit`.
5. Use **Live Run** only when you intend to contact enabled public sources.

Self-Test and Offline/Test Run are network-free. Live Run never logs in or
bypasses CAPTCHA/browser checks.

## Edit scoring rules

Use **Open Keywords Workbook**, edit `config\keywords.xlsx`, save, then click
**Validate Keywords** and **Reload Keywords**. You can add rules, change
weights, choose `contains`/`exact`/bounded `regex`, or set `active` to `N`.

`RESCORE_ALWAYS` recomputes current score, tier, gate, and bucket for all
replayable records. `Keyword_Change_Audit` shows old/new values and rule
attribution. Manual `Status`, `Notes`, `Assigned To`, and Weekly Review Log
entries survive. If the canonical workbook is damaged, only a verified
external last-known-good snapshot may run, with a visible warning.

## Manage sources

Open **Source Checks**. `config\sources.csv` is the one runtime registry.

- Add/edit or enable/disable a source.
- **Validate Configuration** checks only config and URL syntax (no parser or
  network).
- **Offline Parser Test** runs the adapter against a local sanitized fixture.
- **Live Source Test** explicitly contacts only the selected public source and
  is the only operation that can mark it `verified_live`.

Configured or enabled does not mean operational. Read the displayed status and
last test details.

## Manual email alerts

In **Email Alerts**, create/open the import folder, copy approved `.eml` files,
run the import test, then use the email-enabled run action. Tender Finder never
moves/deletes source messages and stores no mailbox password.
