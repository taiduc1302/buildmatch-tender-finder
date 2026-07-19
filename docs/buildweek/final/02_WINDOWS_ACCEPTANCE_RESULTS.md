# Windows Acceptance Results (Phase 4)

## Environment constraint

This session's development environment is headless Linux with no `DISPLAY`,
no `tkinter` C-extension for the active Python interpreter, and no
Windows/PowerShell runtime available (`pwsh`/`powershell.exe` not installed,
and could not be fetched — outbound access to GitHub Releases is blocked by
this session's proxy policy). This is a genuine, conclusively-documented
external blocker for anything requiring an actual Windows desktop or
interactive GUI rendering. It was true in the prior session and remains true
in this one.

## What WAS done given the constraint

1. **Reviewed `scripts/windows_acceptance.ps1` line-by-line** and found a real
   correctness bug: `$ErrorActionPreference = "Stop"` does **not** convert a
   non-zero exit code from an external process (`python.exe`, `pytest`) into a
   terminating PowerShell error — only step 2 (pytest) explicitly checked
   `$LASTEXITCODE`; every other step (offline CI check, Self-Test, package
   audit, release build/verify, the four itemized pytest subsets) could fail
   silently while the script still printed "ALL AUTOMATED CHECKS PASSED".
   Rewrote the script with an `Invoke-Step` helper that checks `$LASTEXITCODE`
   after every step and aborts immediately on the first real failure, so a
   false "PASS" banner is no longer possible. Also hardened the release-zip
   discovery (unique temp dir per run, most-recent-by-timestamp selection
   instead of an arbitrary first match) and added a Python-interpreter
   diagnostic step.
2. **Verified the `.venv\Scripts\python.exe` resolution convention** the
   script relies on against `setup_tenderfinder_environment.bat` and
   `Launch_TENDER_FINDER_GUI.bat` — confirmed correct.
3. **Verified the exact CLI flag names** the script passes to
   `build_clean_release.py` (`--output-dir`), `verify_clean_release.py`
   (positional `zip_path`), and `package_audit.py` (`--mode repo .`) against
   each script's real `argparse` definitions — confirmed correct.
4. **Manual PowerShell syntax review** (function definitions, scriptblock
   invocation via `&`, `$LASTEXITCODE` propagation across `Invoke-Step`,
   `Push-Location`/`Pop-Location` with `try/finally`, string escaping) — could
   not be executed by a real `pwsh` interpreter in this environment; this
   remains a genuine gap requiring the founder to run the script on an actual
   Windows machine.
5. **Ran every automated check the script itself would run**, directly on
   this Linux environment via the equivalent Python invocations (offline CI
   check, full pytest, Self-Test, package audit, clean-release build+verify) —
   all passed (see `06_TEST_AND_ACCEPTANCE_RESULTS.md` /
   `01_FULL_RAW_SWEEP_IMPLEMENTATION.md`). This proves the underlying checks
   are sound; only the PowerShell *wrapper*'s execution on real Windows
   remains unverified.
6. **Confirmed the new GUI widgets construct correctly on real Windows.**
   After pushing this session's changes, the "Offline verification (Windows,
   Python 3.12)" GitHub Actions check (`windows-latest` runner, real tkinter)
   ran the Self-Test, which constructs the full `TenderFinderLauncherApp`
   including the new data-mode banner, preset selector, Refresh Development
   Data button, and the new Ranked Opportunities tab's `ttk.Treeview` and
   selection widgets. **First attempt genuinely failed** —
   `PermissionError: [WinError 32]` during `tempfile.TemporaryDirectory`
   cleanup, caused by two new formula-injection regression tests (and, found
   on inspection, two production code paths) leaving an `openpyxl`
   `read_only` workbook handle open, which Windows (unlike POSIX) refuses to
   delete out from under. Fixed by explicitly closing every such handle; the
   corrected push's CI run passed. This is exactly the kind of defect only a
   real Windows run catches — see `06_REMEDIATION_LOG.md` item 11 and
   `07_REMOTE_PR_AUDIT.md` for the verified-green result.

## What remains genuinely unverified (requires an actual Windows desktop)

* Visual layout quality, button accessibility, dialog behaviour, and the
  Ranked Opportunities table's on-screen selection UX.
* A real interactive click-through of Refresh → Ranked Opportunities → select
  a row → Analyze with AI → export.
* Running `powershell -ExecutionPolicy Bypass -File .\scripts\windows_acceptance.ps1`
  end-to-end on a real Windows machine.

## Founder action required

```powershell
# From the repository root, in PowerShell on a real Windows machine:
powershell -ExecutionPolicy Bypass -File .\scripts\windows_acceptance.ps1
```

Then walk the manual GUI checklist in `docs/buildweek/08_WINDOWS_ACCEPTANCE.md`.
