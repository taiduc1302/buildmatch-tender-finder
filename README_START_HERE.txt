TENDER FINDER - START HERE (INTERNAL WEEKLY BETA)
================================================

1. Double-click Launch_TENDER_FINDER_GUI.bat.
2. First launch installs a private Python environment. Python 3.11+ and
   internet access are required; this is not a self-contained EXE.
3. Open Keywords and click Validate Keywords.
4. Click Run Self-Test. Require PASS, 0 failed, and 0 not-tested fixtures.
5. Use Offline/Test Run first. It contacts no tender sites.
6. Use Live Run only when you intend to contact enabled public sources.

KEYWORDS
--------
Open config\keywords.xlsx from the Keywords tab. Add/change/disable rules,
save, Validate Keywords, then Reload Keywords. Every run rescales replayable
records from the current effective rules (RESCORE_ALWAYS). Inspect
Keyword_Change_Audit for old/new score, tier, and bucket. Manual Status, Notes,
Assigned To, and Weekly Review Log values are preserved.

SOURCES
-------
Open Source Checks. Validate Configuration is config-only; Offline Parser Test
uses a local fixture; Live Source Test explicitly contacts only the selected
public source. Configured/enabled is not the same as verified live.

OUTPUTS
-------
Use Open Workbook or Open Output Folder. Normal outputs, manifests, logs,
settings, backups, and history are beneath C:\tenderfinder_out, outside the
program folder.

IF SOMETHING FAILS
------------------
Run Self-Test again or double-click verify_package.bat. A FAIL is intentional
and honest: use the shown manifest/output path before trusting a workbook.
