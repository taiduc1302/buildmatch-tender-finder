# Windows Acceptance Procedure

The development environment for this branch is headless Linux without tkinter,
so on-screen GUI rendering, live public-network refresh, and live OpenAI calls
must be verified on a Windows desktop by the founder. Everything else is
verified automatically.

## Automated (run this first)

```powershell
# From the repository root, in PowerShell:
.\scripts\windows_acceptance.ps1
```

This runs: offline CI check, full pytest suite, authoritative Self-Test, package
audit, clean-release build + verify, public-snapshot validation/scoring,
contractor presets, mocked OpenAI GUI flow + missing-key + cache, and the refresh
orchestration + rollback + truthful-metrics tests. Exit code 0 = all passed.

## Manual GUI checklist

1. **Clean checkout** — clone the repo fresh (or extract the clean-release ZIP).
2. **Environment setup** — double-click `Launch_TENDER_FINDER_GUI.bat`; it repairs
   the venv via `setup_tenderfinder_environment.bat` and starts the GUI.
3. **GUI launch** — the window opens with no console; the Run tab is visible.
4. **Self-Test** — click **Run Self-Test**; confirm it reports PASS.
5. **Synthetic Demo** — click **Offline/Test Run**; confirm the banner reads
   `SYNTHETIC DEMO DATA` and a workbook opens.
6. **Public Snapshot Demo** — from a terminal:
   `python -c "import sys; sys.path.insert(0, r'01 Code\CONNECTOR_SWEEP'); import tenderfinder_snapshot as s; print(s.promote_snapshot(root='.'))"`
   then reopen the GUI and confirm the banner reads `PUBLIC SNAPSHOT — captured …`.
7. **Refresh Development Data** — select a contractor profile, click **Refresh
   Development Data**; confirm truthful current-run statistics and a live/cached
   banner (needs public network).
8. **Source-health display** — Source Checks tab shows per-source status; confirm
   Vancouver rezoning/dev-permit sources read `needs_configuration` and are not
   selected.
9. **Current-run statistics** — confirm the metrics line reflects this run only.
10. **Data-mode banner** — confirm it updates after each action.
11–13. **Presets** — switch between Civil, Multi-Family Residential, and General
    Contractor; confirm the selector and manifests reflect the choice.
14. **Missing OpenAI key** — with no key set, click **Analyze Selected Opportunity
    with AI**; confirm setup guidance appears and deterministic features still work.
15. **Live OpenAI analysis** — set `OPENAI_API_KEY` (and `OPENAI_MODEL`); confirm a
    structured, evidence-based analysis appears separate from the deterministic score.
16. **Cached OpenAI analysis** — re-analyze the same record; confirm it is served
    from cache (marked cached) without a second API call.
17. **Failed-refresh rollback** — disconnect the network, refresh; confirm the
    previous dataset is retained and the banner reads cached/stale.
18. **Manual-field preservation** — confirm manual triage fields survive a rebuild.
19. **Workbook opening** — confirm Open Workbook/Report/Summary work.
20. **Clean release package startup** — extract the clean-release ZIP and launch it.

## Final status

`COMPLETE_WITH_EXTERNAL_WINDOWS_VERIFICATION_REQUIRED` is appropriate only while
every mandatory automated suite is green (it is) and only the interactive
Windows GUI, live public network, and user-owned OpenAI key remain to verify.
