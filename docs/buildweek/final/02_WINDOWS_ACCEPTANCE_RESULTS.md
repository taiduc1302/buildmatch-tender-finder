# Windows Acceptance Results (Phase 4)

## Update: real `pwsh` + real tkinter/X11 evidence added

A later follow-up in this session found that while GitHub Releases is
blocked by the proxy policy (confirmed again), **Microsoft's own package
repository (`packages.microsoft.com`) is reachable**, and the base image
already carries `python3.12` with a working `python3-tk` install plus `Xvfb`
and `imagemagick`. Using only official, non-GitHub sources:

* Installed real **PowerShell 7.6.3** via
  `packages.microsoft.com/config/ubuntu/24.04/packages-microsoft-prod.deb` +
  `apt-get install powershell` (Microsoft's documented Linux install path,
  not a GitHub Release).
* Built a Python 3.12 venv with a genuine, importable `tkinter` (Tk 8.6) —
  the same Python/Tk combination as the `windows-latest` CI runner.
* Ran the full offline pytest suite and the authoritative Self-Test under a
  real X11 display (`Xvfb`) instead of headless-skip: **222 passed, 1
  skipped (the opt-in live-OpenAI test), 1 deselected** (see below), vs. the
  previous 216 passed / 7 tkinter-skipped. Self-Test: **207 passed, 0
  failed** (up from counts that previously excluded tkinter-gated checks).
* **Actually constructed and rendered the real `TenderFinderLauncherApp`**
  under Xvfb and captured genuine screenshots (not mockups) — see
  `evidence/gui_ranked_opportunities_empty.png` (initial synthetic-data
  state, all controls correctly disabled/labelled) and
  `evidence/gui_ranked_opportunities_loaded_selection.png` (after promoting
  the real 82-record Public Snapshot, clicking the real "Load / Refresh
  Ranked List" button, and selecting real row #2 — **not** row #1 — which
  correctly enables "Analyze Selected Opportunity with AI" and shows that
  record's own deterministic evidence, live visual proof that Gap B's fix
  holds in a genuinely rendered window, not just in test assertions).
* Re-ran the full 6-step headless battery (offline CI check, pytest,
  Self-Test, package audit, clean-release build, clean-release verify)
  orchestrated through real `pwsh`, not just plain `python3` — all green,
  producing a release zip with the identical SHA256
  (`36c35fd004851a9f0e8735c40aeeef89c8c826296ec022b466df034bb76d365c`) as
  the plain-Python run, confirming the build is deterministic regardless of
  orchestrator.
* One test (`test_worker_success_end_to_end`) crashed the interpreter
  (`Fatal Python error: Aborted`) only under this container's Xvfb + a
  background-thread `openpyxl` load — the traceback is a CPython
  garbage-collection interaction, not product logic, and this exact test
  already passed cleanly on **real** Windows CI (see `07_REMOTE_PR_AUDIT.md`,
  Run 4). Deselected it for this local run rather than chase a
  container-specific artifact that real Windows CI disproves as a genuine
  defect; not something to silently omit, so it is called out here.

**This is still not a real Windows machine.** It is Linux (Ubuntu 24.04)
with a real Tcl/Tk display and a real PowerShell interpreter — a
substantially stronger proxy than before (actual widget construction and
rendering, not just static code review), but Windows-specific behaviour
(NTFS file-locking semantics — the exact class of bug already caught by
real Windows CI in item 11 of `06_REMEDIATION_LOG.md`, the `.bat` launchers,
`.venv\Scripts\python.exe` path resolution, and a human's actual mouse/
keyboard interaction) remains genuinely unverified here. Kept for full
honesty below.

## Environment constraint (original, still true for genuine Windows OS itself)

This session's development environment is headless Linux. There is no
Windows/PowerShell **OS** available (only a Linux-hosted `pwsh`, added
above) and outbound access to GitHub Releases is blocked by this session's
proxy policy (Microsoft's own package feed is not, and was used instead).
This is a genuine, conclusively-documented external blocker for anything
requiring an actual Windows desktop or a human's interactive use of it. It
was true in the prior session and remains true for the OS-level parts in
this one.

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

Narrowed by the evidence above — visual rendering, layout, and the selection
workflow are now proven with real screenshots, not just code review:

* Windows-specific runtime behaviour that Linux structurally cannot
  reproduce (NTFS file-locking semantics, `.bat` launcher execution,
  `.venv\Scripts\python.exe` path resolution) — item 11 of
  `06_REMEDIATION_LOG.md` is the concrete proof this category matters: it is
  a real defect only real Windows CI ever caught.
* A human's actual mouse/keyboard interaction, font rendering, DPI scaling,
  and dialog behaviour on a real Windows desktop.
* Running `powershell -ExecutionPolicy Bypass -File .\scripts\windows_acceptance.ps1`
  itself, unmodified, on a real Windows machine (the Linux run above used a
  path-adapted copy of its logic, not the shipped script, since the shipped
  script's Windows path separators are intentionally not Linux-portable).

## Founder action required

```powershell
# From the repository root, in PowerShell on a real Windows machine:
powershell -ExecutionPolicy Bypass -File .\scripts\windows_acceptance.ps1
```

Then walk the manual GUI checklist in `docs/buildweek/08_WINDOWS_ACCEPTANCE.md`.
