# QA Review - patch-5-17 / 0b161cd

## Verdict

**FAIL**

This patch is close, and the core code paths compiled and the regression suite ran successfully in this Windows PowerShell environment. But I found one acceptance-relevant accuracy problem in the patch's self-reported verification, plus one concrete diff hygiene failure. I would not accept the patch as-is until those are fixed and re-verified.

## Findings

### P1 - `AUTONOMOUS_FIXES.md` claims verification that the tests do not actually perform

The patch report overstates what was verified for the GUI close/process-cleanup work.

`[AUTONOMOUS_FIXES.md](C:/t/TENDER_FINDER_Patch_5_0/AUTONOMOUS_FIXES.md)` says:

- the WM_DELETE_WINDOW close path was verified,
- and process death was confirmed "independently via `Get-Process -Id <pid>`".

What I could verify from the code and tests is narrower:

- `[01 Code/CONNECTOR_SWEEP/tests/test_launcher_gui.py](C:/t/TENDER_FINDER_Patch_5_0/01%20Code/CONNECTOR_SWEEP/tests/test_launcher_gui.py)` does directly exercise a real subprocess through `terminate_process_tree()` and `DemoBuildWorker.cancel()`, and checks `proc.poll() is not None`.
- I did **not** find any test that shells out to `Get-Process -Id <pid>`.
- I did **not** find any test that directly exercises `TenderFinderLauncherApp._on_close_requested()` or the WM_DELETE_WINDOW path.

That means the patch's generated verification narrative is stronger than the evidence in the repo. For this repo, that matters: orphaned-process cleanup is a known recurring bug class, and this patch specifically claims to close that loop.

Relevant references:

- `[AUTONOMOUS_FIXES.md](C:/t/TENDER_FINDER_Patch_5_0/AUTONOMOUS_FIXES.md)`
- `[01 Code/CONNECTOR_SWEEP/tenderfinder_launcher_gui.py](C:/t/TENDER_FINDER_Patch_5_0/01%20Code/CONNECTOR_SWEEP/tenderfinder_launcher_gui.py)`
- `[01 Code/CONNECTOR_SWEEP/tests/test_launcher_gui.py](C:/t/TENDER_FINDER_Patch_5_0/01%20Code/CONNECTOR_SWEEP/tests/test_launcher_gui.py)`

### P2 - `git diff --check HEAD~1..HEAD` fails on trailing whitespace in `docs/BC_BID_NETWORK_AUDIT.md`

The committed patch is not diff-clean. `git diff --check HEAD~1..HEAD` reports many trailing-whitespace errors in:

- `[docs/BC_BID_NETWORK_AUDIT.md](C:/t/TENDER_FINDER_Patch_5_0/docs/BC_BID_NETWORK_AUDIT.md)`

This is not a functional defect, but it is a real repo-quality issue and should be cleaned before accepting the patch.

## Open Questions / Assumptions

- I reviewed the patch as the current `HEAD` commit on `patch-5-17` because the working tree is clean and `git diff` against the working tree is empty.
- I treated `HEAD~1..HEAD` as the patch under review because that is the only visible delta to inspect.
- I did not open a live GUI window in this environment. My GUI assessment is based on code review plus the real subprocess tests already present in the repo.

## What Claude changed

Patch `0b161cd` changes three main areas:

- GUI shutdown/process cleanup in `[01 Code/CONNECTOR_SWEEP/tenderfinder_launcher_gui.py](C:/t/TENDER_FINDER_Patch_5_0/01%20Code/CONNECTOR_SWEEP/tenderfinder_launcher_gui.py)`
- generic mirror-name derivation and blocked-status reporting in `[01 Code/CONNECTOR_SWEEP/tenderfinder_demo_three_buckets.py](C:/t/TENDER_FINDER_Patch_5_0/01%20Code/CONNECTOR_SWEEP/tenderfinder_demo_three_buckets.py)`
- regression coverage additions in:
  - `[01 Code/CONNECTOR_SWEEP/tests/test_launcher_gui.py](C:/t/TENDER_FINDER_Patch_5_0/01%20Code/CONNECTOR_SWEEP/tests/test_launcher_gui.py)`
  - `[01 Code/CONNECTOR_SWEEP/tests/test_mirror_name_generic.py](C:/t/TENDER_FINDER_Patch_5_0/01%20Code/CONNECTOR_SWEEP/tests/test_mirror_name_generic.py)`
  - `[01 Code/CONNECTOR_SWEEP/tests/test_bc_bid_status_ux.py](C:/t/TENDER_FINDER_Patch_5_0/01%20Code/CONNECTOR_SWEEP/tests/test_bc_bid_status_ux.py)`

It also regenerates `demo_p517/` outputs, updates `[docs/BC_BID_NETWORK_AUDIT.md](C:/t/TENDER_FINDER_Patch_5_0/docs/BC_BID_NETWORK_AUDIT.md)`, `[docs/GETTING_STARTED.md](C:/t/TENDER_FINDER_Patch_5_0/docs/GETTING_STARTED.md)`, and patch narrative/backlog files.

## What I verified

Environment used:

- Windows PowerShell
- repo root: `C:\t\TENDER_FINDER_Patch_5_0`

Commands actually run:

1. Repo / commit identity
   - `git status --short --branch`
   - `git rev-parse HEAD`
   - `git log -1 --oneline`
   - `git show --stat --oneline --decorate=short HEAD`

2. Diff inspection
   - `git diff --stat`
   - `git diff --name-only`
   - `git diff --check`
   - `git diff --stat HEAD~1..HEAD`
   - `git diff --name-only HEAD~1..HEAD`
   - `git diff --check HEAD~1..HEAD`

3. Compile checks
   - `python -m py_compile "01 Code/CONNECTOR_SWEEP/tenderfinder_launcher_gui.py" "01 Code/CONNECTOR_SWEEP/tenderfinder_demo_three_buckets.py" "01 Code/CONNECTOR_SWEEP/tests/test_launcher_gui.py" "01 Code/CONNECTOR_SWEEP/tests/test_bc_bid_status_ux.py" "01 Code/CONNECTOR_SWEEP/tests/test_mirror_name_generic.py"`
   - Result: passed

4. Test discovery / execution
   - `cmd /c dir /s tests`
   - `python "01 Code/CONNECTOR_SWEEP/tests/test_workbook_quality.py"`
   - `python "01 Code/CONNECTOR_SWEEP/tests/run_regression.py" --all --output-dir "C:\tenderfinder_out\regression_p513"`
   - Result: regression runner completed; workbook-quality test passed

5. Workbook / output verification
   - Opened `[demo_p517/TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx](C:/t/TENDER_FINDER_Patch_5_0/demo_p517/TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx)` with `openpyxl`
   - Verified minimum required sheets exist plus additional sheets
   - Verified funnel counts:
     - BID LATER = `7537`
     - Watchlist = `973`
     - Analyzed = `25119`
   - Verified BC Bid status and source log rows
   - Verified email intake row reports `NO_ALERT_EMAILS_FOUND`

6. Protected-master safety
   - `Get-FileHash -Algorithm SHA256 "00 Master\TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx", "00 Master\TENDER_FINDER_Tender_Intelligence_Working_Master_v7_1_cleaned_urls.xlsx"`
   - Result: hashes match expected protected baselines

7. Secret / package-pollution spot checks
   - `rg -n --hidden -S "(API_KEY|SECRET|TOKEN|PASSWORD|storageState|cookie replay|playwright_state|session cookie)" "docs/BC_BID_NETWORK_AUDIT.md" "demo_p517" "01 Code/CONNECTOR_SWEEP/tenderfinder_demo_three_buckets.py"`
   - Result: no obvious committed credentials/tokens found in reviewed patch files

## Evidence

### Branch / commit / cleanliness

`git status --short --branch`

```text
## patch-5-17
```

`git show --stat --oneline --decorate=short HEAD`

```text
0b161cd (HEAD -> patch-5-17) fix: patch-5-17 GUI subprocess cleanup on close, generic   mirror-name derivation, BC Bid blocked-state UX messaging
...
17 files changed, 804 insertions(+), 76 deletions(-)
```

### Diff hygiene failure

`git diff --check HEAD~1..HEAD`

```text
docs/BC_BID_NETWORK_AUDIT.md:13: trailing whitespace.
docs/BC_BID_NETWORK_AUDIT.md:14: trailing whitespace.
...
docs/BC_BID_NETWORK_AUDIT.md:104: trailing whitespace.
```

### Test coverage really present

`[01 Code/CONNECTOR_SWEEP/tests/run_regression.py](C:/t/TENDER_FINDER_Patch_5_0/01%20Code/CONNECTOR_SWEEP/tests/run_regression.py)` includes the new tests, so they are wired into the regression runner.

The GUI/process tests also do exercise a real subprocess:

- `[01 Code/CONNECTOR_SWEEP/tests/test_launcher_gui.py:87](C:/t/TENDER_FINDER_Patch_5_0/01%20Code/CONNECTOR_SWEEP/tests/test_launcher_gui.py:87)` real process termination test
- `[01 Code/CONNECTOR_SWEEP/tests/test_launcher_gui.py:134](C:/t/TENDER_FINDER_Patch_5_0/01%20Code/CONNECTOR_SWEEP/tests/test_launcher_gui.py:134)` verifies cancelled worker subprocess is no longer running

But I found no `Get-Process` test usage:

`rg -n "Get-Process -Id|_on_close_requested|WM_DELETE_WINDOW" ...`

```text
AUTONOMOUS_FIXES.md:5: ... confirmed via proc.poll() (and independently via `Get-Process -Id <pid>`) ...
01 Code/CONNECTOR_SWEEP/tenderfinder_launcher_gui.py:359:        self.root.protocol("WM_DELETE_WINDOW", self._on_close_requested)
01 Code/CONNECTOR_SWEEP/tenderfinder_launcher_gui.py:474:    def _on_close_requested(self) -> None:
```

No test file line references `Get-Process`, and no test directly invokes `_on_close_requested()`.

### Workbook / invariants

Workbook sheets:

```text
['Executive_Summary', 'BID_NOW_Active_Tenders', 'BID_LATER_Future_Projects', 'New_This_Run', 'Outreach_Tracker', 'Developer_Watchlist', 'Design_Consultants_Reference', 'Tender_Pattern_Analysis', 'Watchlist_Monitor', 'Analyzed_Set_Aside', 'Surrey_Historical_Archive', 'Acquisition_Funnel_And_Speed', 'Source_Run_Log', 'Action_Center', 'Live_Tender_Intake_Plan', 'Email_Setup_Guide', 'Top_Civil_Leads_Printable']
```

Funnel rows from `Acquisition_Funnel_And_Speed`:

```text
('BID NOW - tender candidates', 200)
('BID NOW - civil relevant', 45)
('BID NOW - open civil', 45)
('BC Bid - open civil', 45)
('BID NOW - same-municipality BID LATER cross-links', 31)
('BID LATER - clean future-project leads', 7537)
...
```

Email intake / BC Bid status from `Source_Run_Log`:

```text
('email_alert_intake', 'Email Alert Intake', 'NO_ALERT_EMAILS_FOUND', 0, 0, 0, 0, 0, ...)
('bc_bid_public', 'BC Bid public open opportunities', 'OK_BROWSER_COOKIE_REPLAY', 200, 45, 200, 0, 45.29, ...)
```

Protected masters:

```text
SHA256 CA20ABCA726A31828A2B6033BD8D44A1B4B94B301854BCF0D0C80AFD4E54BC7C  v6
SHA256 A1DD67E0C62473B1CE9F5E46A8F8A3FAFF3A866E716BB96C33C848D217941F3D  v7_1
```

## Acceptance Decision

Do **not** accept patch `0b161cd` as-is.

The code and regression state look generally healthy, and I did not find a Track A count regression or protected-master damage. But the patch's own verification narrative currently claims more than the tests prove, and `git diff --check` is red. Fix those, rerun the relevant tests, and then this should be a straightforward re-review.
