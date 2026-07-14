# QA Review - patch-5-17 / a711a1f

## A. PASS / FAIL / PARTIAL

**PASS**

## B. What Claude claimed

Claude claimed patch `a711a1f` fixes the remaining Patch 5.17 long-path preflight failure by extending the existing safe-output redirect logic to the two log files that previously bypassed it, then reran the full regression suite and got a real exit code `0`.

## C. What I independently verified

I verified this on Windows PowerShell in `C:\t\TENDER_FINDER_Patch_5_0`.

- Current branch: `patch-5-17`
- Current HEAD: `a711a1ff990e2226eef565ee1884fe4558c4786b`
- HEAD commit message:
  - `a711a1f fix: patch-5-17 long-path preflight failure - extend existing   safe-output-dir redirect to the two log files that bypassed it`

Patch scope from `HEAD~1..HEAD` is narrow and matches the claim:

- `[01 Code/CONNECTOR_SWEEP/tenderfinder_live_link_checker.py](C:/t/TENDER_FINDER_Patch_5_0/01%20Code/CONNECTOR_SWEEP/tenderfinder_live_link_checker.py)`
- `[01 Code/CONNECTOR_SWEEP/tests/run_regression.py](C:/t/TENDER_FINDER_Patch_5_0/01%20Code/CONNECTOR_SWEEP/tests/run_regression.py)`

I independently confirmed:

- changed Python files compile
- `[01 Code/CONNECTOR_SWEEP/tests/test_launcher_gui.py](C:/t/TENDER_FINDER_Patch_5_0/01%20Code/CONNECTOR_SWEEP/tests/test_launcher_gui.py)` still passes
- `run_regression.py --all` now passes, including:
  - `Preflight dry-run output test: long`
  - `Verify preflight outputs: long`
- the regression command exited with code `0`, not just a log-level success string
- Track A counts are unchanged in the existing demo workbook:
  - `BID_LATER = 7537`
  - `Watchlist = 973`
  - `Analyzed = 25119`
- protected master hashes still match expected baselines
- BC Bid public scan is still clearly distinguished from email intake
- email intake still honestly reports `NO_ALERT_EMAILS_FOUND`

## D. Commands run and results

### Git / repo state

```powershell
git status --short
git branch --show-current
git rev-parse HEAD
git log -1 --oneline
git diff --stat
git diff --name-only
git diff --check
git diff --stat HEAD~1..HEAD
git diff --name-only HEAD~1..HEAD
```

Results:

- tracked working tree is clean
- two untracked QA artifacts from a prior review session remain:
  - `CLAUDE_FIX_PROMPT_patch-5-17_0b161cd.md`
  - `QA_REVIEW_patch-5-17_0b161cd.md`
- `git diff --check` is clean
- `HEAD~1..HEAD` changes only:
  - `01 Code/CONNECTOR_SWEEP/tests/run_regression.py`
  - `01 Code/CONNECTOR_SWEEP/tenderfinder_live_link_checker.py`

### Compile

```powershell
python -m py_compile "01 Code/CONNECTOR_SWEEP/tenderfinder_raw_sweep.py" "01 Code/CONNECTOR_SWEEP/tenderfinder_link_preflight.py" "01 Code/CONNECTOR_SWEEP/tenderfinder_live_link_checker.py"
```

Result: pass

### Test discovery

```powershell
cmd /c dir /s tests
```

Result: test directories found under `.venv\...` and `01 Code\CONNECTOR_SWEEP\tests`

### Relevant tests

```powershell
python "01 Code/CONNECTOR_SWEEP/tests/test_launcher_gui.py"
```

Result:

```text
[PASS] test_build_demo_command
[PASS] test_parse_demo_build_report
[PASS] test_parse_email_state
[PASS] test_bc_bid_blocked_status_simulated
[PASS] test_bc_bid_ok_status_unchanged
[PASS] test_terminate_process_tree_real_process
[PASS] test_worker_cancel_stops_real_subprocess
[PASS] test_on_close_requested_confirms_and_stops_running_build
[PASS] test_on_close_requested_keeps_running_if_user_declines
[PASS] test_worker_success_end_to_end
Launcher GUI logic test: PASS
```

```powershell
python "01 Code/CONNECTOR_SWEEP/tests/run_regression.py" --all --output-dir "C:\tenderfinder_out\regression_patch517_retry_qa"
```

Result:

```text
[PASS] Preflight dry-run output test: long: exit=0, log=preflight_long.log
[PASS] Verify preflight outputs: long: missing=[], redirected=['TENDER_FINDER_Source_Register_URL_Live_Audit.csv', 'TENDER_FINDER_Source_Register_URL_Live_Audit.xlsx', 'TENDER_FINDER_Source_Register_Fix_Queue.csv', 'TENDER_FINDER_Source_Register_Replacement_Candidates.csv', 'TENDER_FINDER_Source_Register_Cleaned_For_Script.csv', 'TENDER_FINDER_Link_Check_Run_Log.txt', 'TENDER_FINDER_Link_Check_Debug_Log.txt'], files=7, run_log_159=True
...
Report written: C:\tenderfinder_out\regression_patch517_retry_qa\REGRESSION_TEST_REPORT.md
```

The process itself exited with code `0`.

### Protected masters

```powershell
Get-FileHash -Algorithm SHA256 "00 Master\TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx", "00 Master\TENDER_FINDER_Tender_Intelligence_Working_Master_v7_1_cleaned_urls.xlsx"
```

Result:

- v6: `CA20ABCA726A31828A2B6033BD8D44A1B4B94B301854BCF0D0C80AFD4E54BC7C`
- v7_1: `A1DD67E0C62473B1CE9F5E46A8F8A3FAFF3A866E716BB96C33C848D217941F3D`

### Safety / package / output checks

```powershell
git ls-files | rg "(^|/)(\.env(\.|$)|__pycache__|\.pytest_cache|storageState|token|credentials|cookies?)"
```

Result:

- only tracked match from these patterns was:
  - `01 Code/CONNECTOR_SWEEP/.env.tenderfinder.local.example`

```powershell
python -c "import zipfile; ..."
```

Result for `TENDER_FINDER_Patch_5_4_Live_Production_Candidate.zip`:

- no `.git/`
- no `.venv/`
- no `__pycache__/`
- no real `.env`
- only flagged item: `01 Code/CONNECTOR_SWEEP/.env.tenderfinder.local.example`

```powershell
python -c "from openpyxl import load_workbook; ..."
```

Result from `[demo_p517/TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx](C:/t/TENDER_FINDER_Patch_5_0/demo_p517/TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx)`:

- `BID LATER - clean future-project leads = 7537`
- `Watchlist = 973`
- `Analyzed and set aside = 25119`
- `email_alert_intake = NO_ALERT_EMAILS_FOUND`
- `bc_bid_public = OK_BROWSER_COOKIE_REPLAY`

## E. Problems found

- **P3**: two untracked QA markdown files from the prior review session are present in the working tree:
  - `CLAUDE_FIX_PROMPT_patch-5-17_0b161cd.md`
  - `QA_REVIEW_patch-5-17_0b161cd.md`
  These are not part of patch `a711a1f` itself.

- **P3**: `TENDER_FINDER_Patch_5_4_Live_Production_Candidate.zip` still contains `.env.tenderfinder.local.example`.
  This is an example template, not a real secret or credential.

No P0/P1/P2 issues found for patch `a711a1f`.

## F. Acceptance decision

Patch `a711a1f` can be **accepted as-is**.

The fix is real, the regression failure it targeted now passes under direct reproduction, the overall `run_regression.py --all` run exits `0`, the patch scope is narrow and appropriate, and core TENDER_FINDER invariants remain intact.

## G. Ready-to-paste Claude Code fix prompt

No fix required.

Claude patch `a711a1f` was independently verified and can be accepted as-is.
