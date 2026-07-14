# TENDER_FINDER Patch 5.4 - Aider Recovery Handoff

Date: 2026-06-25
Source context: ZCode Patch 5.3 -> 5.4 attempt stopped due to limits during Phase A.

## 0. Bottom line

ZCode did **not** reach Phase B live proof.

It spent the session on Phase A / baseline regression issues caused mostly by Windows path length and one missing test dependency. The current edited `_work` tree is **not final** and should not be packaged as Patch 5.4.

Recommended recovery in Aider:

1. Keep the ZCode-edited files only as reference.
2. Start from a fresh unzip of `TENDER_FINDER_Patch_5_3_Live_Hardened (1).zip` into a very short path, ideally `C:\t54`.
3. Run the baseline commands from the short path.
4. If baseline passes or only has non-blocking long-path/dev-dependency issues, move immediately to live proof.
5. Do not spend the next session perfecting Windows long-path regression architecture unless it blocks live proof from the short path.

Patch 5.4 value = honest live proof + business-readable outputs, not perfect regression internals.

---

## 1. Files involved

Baseline package:

```text
TENDER_FINDER_Patch_5_3_Live_Hardened (1).zip
```

Context files provided to ZCode:

```text
TENDER_FINDER_ZCODE_HANDOFF_FULL_CONTEXT.md
TENDER_FINDER_Tender_Intelligence_Context_Brief_v2.md
```

Working folder used by ZCode:

```text
C:\ZCodeProject\TENDER_FINDER_Patch_5_4_Sandbox\_work\TENDER_FINDER_Patch_5_0
```

Recommended fresh recovery folder for Aider:

```text
C:\t54\TENDER_FINDER_Patch_5_0
```

---

## 2. ZCode's initial assessment

ZCode read both briefs and inspected the package. Its assessment:

- This is a continuation project, not a restart.
- Patch 5.3 is package/regression accepted, but live production proof is still missing.
- Patch 5.3 shipped `test_outputs_p53/` and pre-generated regression outputs.
- Regression report in the package says 24/24 PASS.
- Verify outputs are present.
- No real `.env.tenderfinder.local` / no secrets found.
- Connector registry has 17 entries.
- Several entries are honest stubs/placeholders, not working connectors.
- Source Register is the business universe, connector CSV is the executable subset.
- Raw records are not leads until filtered/scored/routed/reviewed.
- Protected master must not be touched.

ZCode claimed it had live network access and probed:

```text
Surrey RezoningInProcess-Result.pdf -> HTTP 200, 157,720 bytes
Surrey DP-IN-PROCESS.pdf -> HTTP 200, 224,072 bytes
ArcGIS TOL FeatureServer -> HTTP 200
Vancouver ODS issued-building-permits -> HTTP 200
py_compile all modules -> OK
```

This was important because Patch 5.3 live proof was previously deferred.

---

## 3. User decisions answered to ZCode

The following decisions were given:

### 3.1 Master access

Use copied test master only.

Do not write to protected v6 or v7_1 master.

For Patch 5.4, prove promote workflow only against:

```text
TENDER_FINDER_Master_PATCH5_4_WRITE_TEST.xlsx
```

Patch 5.4 final package should be a **Live Production Candidate**, not an actual production master write.

### 3.2 Backlog scope

Do Phase A, B, and C first.

Live proof and operationalization are higher priority than new connector expansion.

Optional Phase D:

- attempt `coquitlam_devapps` first only if clean/low-risk;
- then one Vancouver ODS source only if endpoint/slug is clear.

Do not let backlog work delay live proof.

### 3.3 Live-output footprint

Final outputs should show total acquisition volume.

Rejected/noisy/bulk/manual/held records should remain reviewable.

Do not make final zip unnecessarily huge.

Preferred:

- include full summary counts;
- include business-readable workbooks/reports;
- include reviewable tabs for clean, watchlist, bulk/noisy, rejected/context, manual/P3, failed;
- for very large Vancouver/raw outputs, include capped or compressed evidence if needed;
- do not hide rejected/noisy records just to make the package clean.

---

## 4. Phase A actions actually performed by ZCode

### 4.1 Workspace creation

ZCode tried relative unzip first; failed due to path with spaces and parentheses.

Failed command pattern:

```bash
cd "C:\ZCodeProject\TENDER_FINDER_Patch_5_4_Sandbox" && \
mkdir -p _work && cd _work && \
unzip -o -q "../../TENDER_FINDER_Patch_5_3_Live_Hardened (1).zip"
```

Then used absolute path and extraction succeeded:

```bash
cd "C:\ZCodeProject\TENDER_FINDER_Patch_5_4_Sandbox" && \
rm -rf _work && mkdir -p _work && \
unzip -o -q "C:\ZCodeProject\TENDER_FINDER_Patch_5_4_Sandbox\TENDER_FINDER_Patch_5_3_Live_Hardened (1).zip" -d "_work"
```

### 4.2 Package state checks

ZCode reported:

- secrets posture clean;
- no stale nested package issue found;
- no `_ss` archive snapshot issue found;
- protected master hashes matched between `_work` and `_inspect`.

Recorded hashes:

```text
v6:   fc2c40ce...07736
v7_1: 90e11c6e...adcdc9
```

### 4.3 Compile commands

ZCode ran:

```bash
cd "C:\ZCodeProject\TENDER_FINDER_Patch_5_4_Sandbox\_work\TENDER_FINDER_Patch_5_0\01 Code\CONNECTOR_SWEEP" && \
python -m py_compile tenderfinder_raw_sweep.py tenderfinder_live_link_checker.py tenderfinder_surrey_inprocess.py tenderfinder_source_registry.py tenderfinder_master_io.py tenderfinder_guards.py tenderfinder_bulk_io.py tenderfinder_link_preflight.py
```

Result:

```text
PASS - all 8 modules compile clean
```

It also compiled test scripts:

```bash
python -m py_compile tests/run_regression.py tests/test_routing_gates.py tests/test_surrey_pdf_parser.py tests/make_surrey_fixtures.py tests/run_failure_tests.py tests/test_search_api_errors.py
```

Result:

```text
PASS - all 6 test scripts compile clean
```

### 4.4 Connector list

Command:

```bash
python tenderfinder_raw_sweep.py --list > _work_list.log 2>&1
```

Result:

```text
exit=0
17 connectors confirmed
```

Cosmetic issue found:

```text
surrey_planning_reportsready_for_load
```

Diagnosis:

- `fetch_type` value `surrey_planning_reports` is 22 characters;
- `--list` column width for FETCH TYPE is 20;
- text bleeds into access-status column;
- underlying CSV is correct;
- non-functional display bug.

---

## 5. Regression failures and attempted fixes

### 5.1 First `--all` run

Command:

```bash
cd "C:\ZCodeProject\TENDER_FINDER_Patch_5_4_Sandbox\_work\TENDER_FINDER_Patch_5_0\01 Code\CONNECTOR_SWEEP" && \
START=$(date +%s) && \
python tests/run_regression.py --all > _work_regall.log 2>&1; \
RC=$?; END=$(date +%s); echo "exit=$RC elapsed=$((END-START))s"
```

Result:

```text
exit=1 elapsed=1s
```

Diagnosis:

- not a business logic failure;
- Windows MAX_PATH / `shutil.rmtree` cleanup issue;
- harness tried to remove existing `test_outputs_p53` tree;
- deep nested path exceeded Windows behavior around 260 characters;
- `shutil.rmtree(self.output_dir)` in `tests/run_regression.py` failed with directory-not-empty / long-path behavior.

Specific root-cause statement from ZCode:

```text
Regression.__init__ calls shutil.rmtree(self.output_dir)
The test intentionally creates a very_long_output_path.../deep_nested_folder_level_03/link_audit_out_v7_1_live tree
On Windows, shutil.rmtree without \\?\ prefix cannot enumerate/delete over-260 paths
```

### 5.2 Change attempted in `tests/run_regression.py`

File changed:

```text
TENDER_FINDER_Patch_5_0/01 Code/CONNECTOR_SWEEP/tests/run_regression.py
```

Intended change:

- add `import os` at module level;
- add helper `_rmtree_longpath_safe()`;
- replace direct `shutil.rmtree(self.output_dir)` call in `Regression.__init__` with `_rmtree_longpath_safe(self.output_dir)`.

Approximate helper logic intended by ZCode:

```python
def _rmtree_longpath_safe(path):
    path = Path(path)
    if not path.exists():
        return
    if os.name == "nt":
        try:
            shutil.rmtree("\\\\?\\" + str(path.resolve()))
            return
        except Exception:
            pass
    shutil.rmtree(path)
```

ZCode tested the helper against a fresh deep tree:

```text
bad deep dir present: YES
files in deepest dir: 7
exists before: True
exists after: False
HELPER RESULT: PASS
```

### 5.3 Second `--all` run after `run_regression.py` fix

Command:

```bash
python tests/run_regression.py --all > _work_regall.log 2>&1
```

Result:

```text
21/24 PASS
```

Meaning:

- the cleanup/rmtree fix worked;
- regression no longer aborted immediately;
- three failures surfaced.

Diagnosed failures:

#### FAIL 1 - `reportlab` dependency

The Surrey parser test imports `reportlab` around line 104 to synthesize a one-page empty PDF used to test the debug-artifact-on-empty path.

Important note:

```text
Actual parser tests all passed 13/13.
Failure was fixture-generation dependency, not production parser logic.
```

Options:

- install `reportlab` and document it as dev/test dependency;
- or replace that test with a checked-in tiny PDF/no-extra-dependency fixture.

ZCode chose the fast route: install/use `reportlab`.

No confirmed requirements file update was completed before limits ended.

#### FAIL 2 - preflight long-path mkdir

The preflight long-path test failed with:

```text
WinError 206: filename or extension is too long
```

Diagnosis:

- `path.parent.mkdir(parents=True, exist_ok=True)` inside `_safe_atomic_write` ran before long-path redirect/safe handling;
- `args.output_dir.mkdir(parents=True, exist_ok=True)` in `tenderfinder_live_link_checker.py:main()` also directly called normal mkdir;
- both fail on the deep regression path in this Windows workspace.

#### Third failure

ZCode grouped the remaining failures as environment/deployment issues. After reportlab and mkdir changes, it got to 22/24, leaving one preflight long-path issue.

### 5.4 Changes attempted in `tenderfinder_live_link_checker.py`

File changed:

```text
TENDER_FINDER_Patch_5_0/01 Code/CONNECTOR_SWEEP/tenderfinder_live_link_checker.py
```

Initial intended change:

- add `_mkdir_longpath_safe()` helper near `_safe_atomic_write()`;
- use it in `_safe_atomic_write()` before writing files;
- use it in `main()` where `args.output_dir.mkdir(parents=True, exist_ok=True)` was called.

Approximate helper intended by ZCode:

```python
def _mkdir_longpath_safe(path: Path) -> None:
    if os.name == "nt":
        try:
            Path("\\\\?\\" + str(Path(path).resolve())).mkdir(parents=True, exist_ok=True)
            return
        except Exception:
            pass
    Path(path).mkdir(parents=True, exist_ok=True)
```

Compile check after first mkdir fix:

```bash
python -m py_compile tenderfinder_live_link_checker.py tests/run_regression.py
```

Result:

```text
compile OK
```

### 5.5 Third `--all` run after `reportlab` + mkdir fix

Command:

```bash
python tests/run_regression.py --all > _work_regall2.log 2>&1
```

Result:

```text
22/24 PASS
```

ZCode conclusion:

- reportlab issue fixed;
- `_mkdir_longpath_safe` fixed the mkdir failure;
- one preflight long-path failure remained.

Remaining failure:

```text
logging.FileHandler at line ~303 failed because Python built-in open() inside FileHandler._open() could not handle the long path / prefixed path reliably.
```

ZCode then started changing debug log path handling and `_safe_atomic_write()` behavior.

### 5.6 Incomplete / risky edits at the end

At the end, ZCode was still inside `tenderfinder_live_link_checker.py` and had not finished. Reported changes included:

```text
1 file changed
+51 -25
```

Likely areas touched:

- `_mkdir_longpath_safe()` helper;
- `_safe_atomic_write()`;
- debug log path setup before `setup_logging()`;
- `shutil.move()` call around line ~2010;
- fallback redirect behavior to `C:\tenderfinder_tmp`;
- possibly logic around whether redirected files are returned at original path vs temp path.

Important:

This state is probably incomplete and should not be trusted as final.

ZCode itself realized the issue:

```text
Regression expects files at the original deep path.
_safe_atomic_write redirects files to C:\tenderfinder_tmp when parent path is too long.
Therefore validator cannot find them.
```

It had not completed or verified the final fix before limits ended.

---

## 6. What was NOT completed

ZCode did **not** complete:

- Phase A green baseline;
- final 24/24 regression;
- verify outputs 7/7 after edits;
- Phase B live proof;
- Surrey live review;
- Vancouver live routing proof;
- Township Langley / Maple Ridge live run;
- all17 review-only;
- 159-source preflight live;
- copied-master promote test;
- Patch 5.4 reports;
- final package.

No final Patch 5.4 zip was produced.

---

## 7. Recommended Aider strategy

Do **not** continue blindly from the half-edited `_work` tree.

Use this strategy:

### Step 1 - Save current ZCode diff for reference

If the `_work` tree is still available:

```bash
cd "C:\ZCodeProject\TENDER_FINDER_Patch_5_4_Sandbox\_work\TENDER_FINDER_Patch_5_0"
git diff > C:\ZCodeProject\TENDER_FINDER_Patch_5_4_Sandbox\ZCODE_PARTIAL_DIFF.patch
```

If no git repo exists:

```bash
copy "01 Code\CONNECTOR_SWEEP\tests\run_regression.py" "C:\ZCodeProject\TENDER_FINDER_Patch_5_4_Sandbox\run_regression_ZCODE_PARTIAL.py"
copy "01 Code\CONNECTOR_SWEEP\tenderfinder_live_link_checker.py" "C:\ZCodeProject\TENDER_FINDER_Patch_5_4_Sandbox\tenderfinder_live_link_checker_ZCODE_PARTIAL.py"
```

### Step 2 - Start fresh from short path

```powershell
mkdir C:\t54
Expand-Archive -LiteralPath "C:\ZCodeProject\TENDER_FINDER_Patch_5_4_Sandbox\TENDER_FINDER_Patch_5_3_Live_Hardened (1).zip" -DestinationPath "C:\t54" -Force
cd "C:\t54\TENDER_FINDER_Patch_5_0\01 Code\CONNECTOR_SWEEP"
```

### Step 3 - Run baseline from short path

```powershell
python -m py_compile tenderfinder_raw_sweep.py tenderfinder_live_link_checker.py tenderfinder_surrey_inprocess.py tenderfinder_source_registry.py tenderfinder_master_io.py tenderfinder_guards.py tenderfinder_bulk_io.py tenderfinder_link_preflight.py
python tenderfinder_raw_sweep.py --list
python tests\run_regression.py --all
python tests\run_regression.py --verify-outputs --output-dir "..\..\test_outputs_p53"
```

If `--all` passes from short path, do not import ZCode long-path changes.

If only `reportlab` fails:

```powershell
pip install reportlab
```

Then document it in a dev setup note or `requirements-dev.txt`:

```text
reportlab
```

If long-path still fails from `C:\t54`, prefer the minimal `run_regression.py` cleanup helper only. Avoid broad changes to `tenderfinder_live_link_checker.py` unless preflight live proof cannot run.

### Step 4 - Move directly to Phase B live proof

Create output folder:

```powershell
mkdir C:\tenderfinder_out\patch5_4_live
```

Run, without `TENDER_FINDER_OFFLINE_FIXTURES`:

```powershell
python tenderfinder_raw_sweep.py --only surrey_planning_reports --review-only --out "C:\tenderfinder_out\patch5_4_live\surrey_live_review.xlsx"
python tenderfinder_raw_sweep.py --only van_building_permits --review-only --out "C:\tenderfinder_out\patch5_4_live\van_permits_live_review.xlsx"
python tenderfinder_raw_sweep.py --only twp_langley_devactivity,maple_ridge_devapps --review-only --out "C:\tenderfinder_out\patch5_4_live\core_live_review.xlsx"
python tenderfinder_raw_sweep.py --review-only --out "C:\tenderfinder_out\patch5_4_live\all17_live_review.xlsx"
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7_1_cleaned_urls.xlsx" --preflight-links --preflight-no-search --preflight-output-dir "C:\tenderfinder_out\patch5_4_live\preflight_159_live" --preflight-timeout 20 --preflight-retries 2 --preflight-workers 6
```

### Step 5 - Produce Patch 5.4 proof report

Create:

```text
PATCH_5_4_LIVE_PROOF_REPORT.md
PATCH_5_4_CHANGELOG.md
PATCH_5_4_CONNECTOR_STATUS_MATRIX.csv
PATCH_5_4_SOURCE_COVERAGE_SUMMARY.csv
PATCH_5_4_ACQUISITION_FUNNEL_SUMMARY.csv
REGRESSION_TEST_REPORT_PATCH_5_4.md
```

Minimum required metrics:

```text
Surrey rows pulled / normalized / clean / failed
Vancouver pulled / strong / watchlist / bulk / noisy / clean eligible
Township Langley rows
Maple Ridge rows
all17 review-only status
preflight output files created
fixture fallback used? yes/no
protected master hash before/after
```

---

## 8. Aider prompt to paste

Paste this into Aider after adding the relevant files:

```text
You are continuing TENDER_FINDER Patch 5.4 after a failed ZCode run.

Do not start from scratch conceptually, but do start from a fresh unzip of TENDER_FINDER_Patch_5_3_Live_Hardened (1).zip in a short path, preferably C:\t54.

Read:
- TENDER_FINDER_ZCODE_HANDOFF_FULL_CONTEXT.md
- TENDER_FINDER_Tender_Intelligence_Context_Brief_v2.md
- TENDER_FINDER_AIDER_HANDOFF_PATCH54_RECOVERY.md

The previous ZCode run did not reach live proof. It got stuck in Phase A Windows long-path regression issues.

Partial ZCode changes were attempted in:
- tests/run_regression.py
- tenderfinder_live_link_checker.py

Treat those changes as reference only, not final.

Main objective:
Produce TENDER_FINDER_Patch_5_4_Live_Production_Candidate with honest live proof.

Do not write to protected v6 or v7_1 master.
Do not use offline fixtures as live proof.
Do not treat Vancouver bulk/noisy permit rows as clean Future_Project leads.
Do not hide rejected/bulk/noisy/manual/failed records.

Immediate plan:
1. Fresh unzip to C:\t54.
2. Run baseline commands from short path.
3. If baseline passes or only has non-blocking dev-dependency issues, proceed immediately to live proof.
4. Do not spend time perfecting Windows long-path regression architecture unless it blocks live proof from C:\t54.
5. Run Surrey, Vancouver permits, Township Langley + Maple Ridge, all17 review-only, and 159-source preflight live.
6. Create live_outputs_p54 and PATCH_5_4_LIVE_PROOF_REPORT.md.
7. Then decide whether to do copied-master promote test.

Commands:

cd C:\t54\TENDER_FINDER_Patch_5_0\01 Code\CONNECTOR_SWEEP

python -m py_compile tenderfinder_raw_sweep.py tenderfinder_live_link_checker.py tenderfinder_surrey_inprocess.py tenderfinder_source_registry.py tenderfinder_master_io.py tenderfinder_guards.py tenderfinder_bulk_io.py tenderfinder_link_preflight.py
python tenderfinder_raw_sweep.py --list
python tests\run_regression.py --all
python tests\run_regression.py --verify-outputs --output-dir "..\..\test_outputs_p53"

mkdir C:\tenderfinder_out\patch5_4_live

python tenderfinder_raw_sweep.py --only surrey_planning_reports --review-only --out "C:\tenderfinder_out\patch5_4_live\surrey_live_review.xlsx"
python tenderfinder_raw_sweep.py --only van_building_permits --review-only --out "C:\tenderfinder_out\patch5_4_live\van_permits_live_review.xlsx"
python tenderfinder_raw_sweep.py --only twp_langley_devactivity,maple_ridge_devapps --review-only --out "C:\tenderfinder_out\patch5_4_live\core_live_review.xlsx"
python tenderfinder_raw_sweep.py --review-only --out "C:\tenderfinder_out\patch5_4_live\all17_live_review.xlsx"
python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7_1_cleaned_urls.xlsx" --preflight-links --preflight-no-search --preflight-output-dir "C:\tenderfinder_out\patch5_4_live\preflight_159_live" --preflight-timeout 20 --preflight-retries 2 --preflight-workers 6

Report row counts and output files. Do not claim live success unless live outputs prove it.
```

---

## 9. Known safe vs risky changes from ZCode

### Probably safe / useful

`tests/run_regression.py` long-path cleanup helper:

- fixes Windows cleanup of deep `test_outputs_p53` tree;
- test harness only;
- does not affect production runner behavior.

Documenting or installing `reportlab` as dev/test dependency:

- likely fine;
- affects Surrey synthetic empty-PDF test only;
- should be in `requirements-dev.txt` or setup notes if kept.

### Risky / incomplete

`tenderfinder_live_link_checker.py` long-path rewrite:

- ZCode was still modifying this when limits ended;
- touched `_safe_atomic_write`, `mkdir`, debug log path, and redirect behavior;
- not verified to 24/24;
- could break preflight output paths;
- do not package without review and tests.

---

## 10. Current best decision

The best next move is not to continue debugging the deep-path regression in the long ZCode workspace.

Use a fresh short path and run live proof.

If Aider has time later, cleanly re-implement only the minimal Windows robustness pieces that are proven necessary.

---

## 11. Full ZCode prompt/action algorithm from the chat

This section preserves the practical ZCode operating sequence discussed before switching to Aider. It is included for context only. For Aider, the recovery strategy in sections 7-10 remains the priority.

### 11.1 Intended ZCode setup flow

1. Create a new ZCode task/workspace.
2. Attach these files:

```text
TENDER_FINDER_Patch_5_3_Live_Hardened (1).zip
TENDER_FINDER_ZCODE_HANDOFF_FULL_CONTEXT.md
TENDER_FINDER_Tender_Intelligence_Context_Brief_v2.md
```

3. Keep the initial mode as `Ask before changes`.
4. Use `GLM-5.2 Max` or the strongest available model for the first planning pass.
5. Do not attach the whole chat transcript as primary context unless needed, because it contains old turns, corrections, and extra noise.
6. Start with a read-only understanding prompt.
7. Only after ZCode proves it understands the project, allow implementation.

### 11.2 First read-only ZCode prompt

```text
I am giving you an existing working project. Do not start from scratch.

Please first read these attached files fully:
1. TENDER_FINDER_ZCODE_HANDOFF_FULL_CONTEXT.md
2. TENDER_FINDER_Tender_Intelligence_Context_Brief_v2.md

Also inspect the attached baseline package:
TENDER_FINDER_Patch_5_3_Live_Hardened (1).zip

Do not edit code yet.

First respond only with:
1. Your understanding of the current project.
2. Current Patch 5.3 baseline status.
3. What should be preserved.
4. What looks weak or incomplete.
5. Your proposed Patch 5.4 plan.
6. Maximum 3 blocking questions.

Important:
This is not a restart.
This is a high-autonomy continuation from Patch 5.3 to Patch 5.4 Live Production Candidate.
```

### 11.3 What the first ZCode answer needed to prove

Before allowing implementation, ZCode needed to show that it understood:

```text
1. Do not start from zero.
2. Patch 5.3 is the baseline.
3. Patch 5.4 goal is Live Production Candidate.
4. The goal is not only 16/17 coded connectors; it is the full source universe / acquisition funnel.
5. Rejected, noisy, bulk, manual, failed, and held records must remain reviewable.
6. Offline fixtures cannot be used as live proof.
7. Protected v6/v7_1 master must not be written.
8. Vancouver bulk/noisy permits must not become clean Future_Project leads.
```

### 11.4 Answers given to ZCode's blocking questions

These answers were actually given in the session:

```text
Good assessment. Your understanding is correct.

Answers to your blocking questions:

1. Master access:
Use copied test master only.
Do not write to protected v6 or v7_1 master.
For Patch 5.4, prove the promote workflow only against:
TENDER_FINDER_Master_PATCH5_4_WRITE_TEST.xlsx

The final package should be a Live Production Candidate, not an actual production master write.

2. Backlog scope:
Do Phase A, B, and C first.
Live proof and operationalization are higher priority than new connector expansion.

For Phase D, you may attempt 1-2 backlog connectors only if they are clean and low-risk.
Default priority:
- coquitlam_devapps first
- then one Vancouver ODS source only if the endpoint/slug is clear

Do not let backlog connector work delay or destabilize live proof.
If a connector is not clearly fixable, keep the honest stub/status and document next action.

3. Live-output footprint:
I want total acquisition volume shown clearly.
I also want rejected, noisy, bulk, manual, and held records to remain reviewable.

But do not make the final zip unnecessarily huge.

Preferred approach:
- Include full summary counts.
- Include business-readable workbooks/reports.
- Include reviewable tabs for clean, watchlist, bulk/noisy, rejected/context, manual/P3, failed.
- For very large Vancouver/raw outputs, include capped or compressed evidence if needed, but preserve enough row-level data to audit routing.
- Do not hide rejected or noisy records just to keep the package clean.
- If full raw live output is too large, keep full local output in live_outputs_p54_full or document its path, and include a summarized/capped package copy.

Proceed with Phase A first:
- create clean Patch 5.4 workspace;
- verify fresh baseline;
- run compile/list/regression/verify-output commands;
- do not edit code yet unless a baseline command fails.

After Phase A, report results before moving to Phase B.
```

### 11.5 Initial master specification intended for ZCode

This was the broader working spec discussed for ZCode. It remains useful as context for Aider if a broader autonomous pass is attempted later.

```text
Your role:
High-autonomy continuation engineer.

You are allowed to refactor, improve reports, improve source coverage, improve connector status, improve dashboard/workbook outputs, and improve the review/promote workflow if it clearly supports the business goal.

But do not start from zero.
Preserve the useful working Patch 5.3 functionality unless you prove a better replacement.

North star:
Build a practical TENDER_FINDER tender / future-project intelligence system that helps a civil / earthworks contractor find useful opportunities earlier and more consistently.

This is not just a regression-hardening task.
This is not just a list of 16/17 websites.
This is not just a clean lead export.

The final system should show the full acquisition funnel:

Source Universe
-> Source Register coverage
-> Coded connectors
-> Working automated sources
-> Semi-automated / PDF / RSS / HTML candidates
-> Manual / P3 / login / paid sources
-> Records pulled
-> Records normalized
-> Clean TENDER_FINDER candidates
-> Watchlist candidates
-> Bulk/noisy records
-> Rejected/context records
-> Failed/manual sources
-> Safe-to-promote rows

Important user requirement:
I want as many useful sources as practical, not only the current coded connector list.
I want final outputs to show total acquisition volume, not only clean leads.
I want to review records that the code rejected, held, routed to bulk, routed to manual, or classified as noisy/context/wrong-layer.
Rejected does not mean invisible.

Hard boundaries:
1. Do not overwrite the protected original master workbook.
2. Do not silently overwrite any workbook.
3. Do not write to v6.
4. Do not use offline fixtures as live proof.
5. Do not silently replace failed live sources with fixture data.
6. Do not treat Vancouver bulk/noisy permit rows as clean Future_Project leads.
7. Do not call Source Register rows coded connectors.
8. Do not call URL-alive harvestable source.
9. Do not hide failed connectors by routing everything to manual.
10. Do not claim a connector is live-working unless live output proves it.
11. Do not remove rejected/held records; preserve them with reason.
12. Do not remove Run_Log, Source_QA, raw outputs, or Bulk_Intake_Raw evidence without replacing them with something clearly better.
13. Do not scrape login-only portals.
14. Do not bypass paid portals.
15. Do not invent endpoints.
16. Do not silently use wrong layers.
17. Do not mix Active_Tenders and Future_Projects.
18. Do not promote raw bulk records as verified leads.
19. Do not produce audit-only reports; improve the system and prove it.

Patch 5.4 priorities:
1. Preserve and verify Patch 5.3 baseline.
2. Run live proof where environment allows.
3. Fix Surrey live PDF extraction if needed.
4. Confirm Vancouver permit routing live.
5. Improve useful automated/semi-automated coverage from existing Source Register and connector backlog.
6. Produce business-readable acquisition funnel report/dashboard.
7. Preserve rejected/held/manual/failed records for review.
8. Prove copied-master promote workflow using ACCEPT-only rows.
9. Package everything cleanly with reports and test outputs.
```

### 11.6 Baseline verification commands originally planned for ZCode

```text
From:
TENDER_FINDER_Patch_5_0\01 Code\CONNECTOR_SWEEP

Run:

python -m py_compile tenderfinder_raw_sweep.py tenderfinder_live_link_checker.py tenderfinder_surrey_inprocess.py tenderfinder_source_registry.py tenderfinder_master_io.py tenderfinder_guards.py tenderfinder_bulk_io.py tenderfinder_link_preflight.py

python tenderfinder_raw_sweep.py --list

python tests\run_regression.py --all

python tests\run_regression.py --verify-outputs --output-dir "..\..\test_outputs_p53"

Expected:
--all = 24/24 PASS
--verify-outputs = 7/7 PASS
```

### 11.7 Fast autonomous mode prompt actually given after delays

This was the prompt used after it became clear that pausing after every Phase A issue was burning limits:

```text
Good. Switch to fast autonomous mode.

You do not need to pause after every baseline/environment issue.

Main goal:
Move the project forward to Patch 5.4 Live Production Candidate as efficiently as possible.

You are authorized to:
- fix baseline regression/environment issues;
- fix Windows long-path issues;
- add missing dev/test dependency documentation if needed;
- make small code changes required to get Phase A green;
- immediately continue to Phase B live proof after Phase A passes;
- create reports/workbooks/summaries needed for Patch 5.4;
- make practical decisions without asking me every time.

Do not stop for approval unless you are about to:
1. write to protected v6 or v7_1 master;
2. remove major existing functionality;
3. change core routing/business rules;
4. scrape login/paid sources;
5. make a broad architecture rewrite.

For everything else, proceed.

Priority order:
1. Get Phase A green as fast as possible.
2. Run Phase B live proof immediately after Phase A passes.
3. Generate live_outputs_p54.
4. Generate PATCH_5_4_LIVE_PROOF_REPORT.md.
5. Confirm Surrey live result.
6. Confirm Vancouver routing live.
7. Confirm Township Langley and Maple Ridge live.
8. Run all17 review-only.
9. Run 159-source preflight.
10. Then do copied-master promote test only if time/limits allow.
11. Package Patch 5.4 candidate.

For the current issues:
- If reportlab is needed for tests, install it if available and document it in requirements-dev or a setup note.
- If a no-dependency fixture fix is faster and reliable, do that instead.
- Fix Windows long-path cleanup/mkdir in the codebase.
- Keep the fixes narrow.
- Do not spend too much time perfecting test architecture.

After Phase A is green, do not wait for my approval. Proceed directly to Phase B live proof.

Live proof rules:
- no offline fixtures;
- no master write;
- copied outputs only;
- preserve rejected/bulk/noisy/manual/failed records;
- show total pulled/normalized/clean/watchlist/bulk/rejected/manual/failed counts.

Package goal:
TENDER_FINDER_Patch_5_4_Live_Production_Candidate.zip

Final response should include:
- what you fixed;
- commands run;
- pass/fail results;
- live row counts;
- output files created;
- remaining risks;
- final zip if completed.

Proceed now.
```

### 11.8 Recovery prompt after ZCode limits ended

This is the most important ZCode recovery prompt if returning to ZCode later. For Aider, sections 7-10 are preferred.

```text
Stop spending time on long-path architecture.

We lost too much time in Phase A. The main Patch 5.4 value is live proof, not perfecting Windows long-path regression internals.

Current status from the previous run:
- You created a working tree under C:\ZCodeProject\TENDER_FINDER_Patch_5_4_Sandbox\_work.
- You found Phase A failures caused by Windows path length and missing reportlab.
- You edited tests/run_regression.py and tenderfinder_live_link_checker.py.
- You did not reach Phase B live proof yet.
- Do not assume the current edited code is final.

Immediate recovery plan:

1. Save current diff/changed files for reference.
2. Do not package the half-edited state yet.
3. Create a new short-path working copy from the original zip:

C:\t54

Use:
TENDER_FINDER_Patch_5_3_Live_Hardened (1).zip

4. Extract fresh into C:\t54.
5. Run the baseline commands from the short path first.

From:
C:\t54\TENDER_FINDER_Patch_5_0\01 Code\CONNECTOR_SWEEP

Run:

python -m py_compile tenderfinder_raw_sweep.py tenderfinder_live_link_checker.py tenderfinder_surrey_inprocess.py tenderfinder_source_registry.py tenderfinder_master_io.py tenderfinder_guards.py tenderfinder_bulk_io.py tenderfinder_link_preflight.py

python tenderfinder_raw_sweep.py --list

python tests\run_regression.py --all

python tests\run_regression.py --verify-outputs --output-dir "..\..\test_outputs_p53"

Important:
If --all passes from C:\t54, do not continue fixing long-path code.
Move immediately to live proof.

If --all fails only because reportlab is missing:
Install/report the dev dependency or skip only the non-critical empty-PDF synthetic test with documentation.
Do not spend more than one iteration on this.

If --all fails only because of long-path cleanup/preflight:
Use the shortest working path and proceed.
Do not redesign tenderfinder_live_link_checker.
Document long-path regression as a known Windows environment issue for Patch 5.4.

Main priority now:
Run Phase B live proof.

Do not use TENDER_FINDER_OFFLINE_FIXTURES.
Do not write to master.
Do not touch protected v6 or v7_1.

Create:

C:\tenderfinder_out\patch5_4_live

Then run:

python tenderfinder_raw_sweep.py --only surrey_planning_reports --review-only --out "C:\tenderfinder_out\patch5_4_live\surrey_live_review.xlsx"

python tenderfinder_raw_sweep.py --only van_building_permits --review-only --out "C:\tenderfinder_out\patch5_4_live\van_permits_live_review.xlsx"

python tenderfinder_raw_sweep.py --only twp_langley_devactivity,maple_ridge_devapps --review-only --out "C:\tenderfinder_out\patch5_4_live\core_live_review.xlsx"

python tenderfinder_raw_sweep.py --review-only --out "C:\tenderfinder_out\patch5_4_live\all17_live_review.xlsx"

python tenderfinder_raw_sweep.py --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v7_1_cleaned_urls.xlsx" --preflight-links --preflight-no-search --preflight-output-dir "C:\tenderfinder_out\patch5_4_live\preflight_159_live" --preflight-timeout 20 --preflight-retries 2 --preflight-workers 6

Report:
- Surrey rows pulled / normalized / clean / failed
- Vancouver pulled / strong / watchlist / bulk / noisy / clean eligible
- Township Langley rows
- Maple Ridge rows
- all17 status
- preflight files created
- whether any fixture fallback happened
- exact output files created

After live proof:
Create PATCH_5_4_LIVE_PROOF_REPORT.md.

Only after that decide whether to return to regression polish.

Patch 5.4 goal is:
Live Production Candidate with honest live proof and business-readable outputs.

Do not burn more time on perfect test architecture unless it blocks live proof.
```
