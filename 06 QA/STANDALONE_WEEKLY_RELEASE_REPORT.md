# TENDER_FINDER standalone weekly release report

**Release verdict: PASS**

Date: 2026-07-14 (America/Vancouver)
Branch: `main`
Reviewed base commit: `1f649d1f275a91e42ce36cbdf9b8c7997c1e8926`

## Founder outcome

TENDER_FINDER is now a standalone Windows program that opens from
`Launch_TENDER_FINDER_GUI.bat`, offers Live Run and Offline/Test Run, validates
the founder-editable `config/keywords.xlsx`, manages one canonical source
registry, and runs an honest offline Self-Test from the GUI. Keyword edits are
applied to old and new records on the next run. Founder-owned Status, Notes,
Assigned To, and Weekly Review Log data survive rescoring and bucket moves, and
the workbook exposes score/tier/bucket changes in `Keyword_Change_Audit`.

## Acceptance checklist

- [x] **Codex targeted review completed and all blocking/high findings resolved.**
- [x] External Claude review is optional future defence-in-depth, not a gate.
- [x] Double-click Windows launcher opens the working GUI without a terminal.
- [x] GUI exposes Live Run, Offline/Test Run, Validate Keywords, and Self-Test.
- [x] GUI Self-Test reports real PASS/FAIL counts from the shared engine.
- [x] `keywords.xlsx` supports editable `keyword`, `match_type`, `weight`,
  `category`, `explanation`, and `active` fields and fails loudly when invalid.
- [x] Editable regex is bounded and rejects unsafe constructs.
- [x] `RESCORE_ALWAYS` recomputes every recomputable keyword-derived field for
  replayed, imported, and newly collected records at one pipeline stage.
- [x] Manual Status/Notes/Assigned To and Weekly Review Log values persist.
- [x] Score, tier, and bucket changes are visible in `Keyword_Change_Audit`.
- [x] `config/sources.csv` is the single configurable source registry.
- [x] GUI supports source Add/Edit/Enable/Disable/Validate/Offline Test/Live Test.
- [x] Display-independent engine is separate from the Tk GUI.
- [x] Runtime outputs, state, settings, and email intake data stay outside repo.
- [x] One controlled Surrey public-source live proof passed without credentials.
- [x] Frozen legacy `01 Code/tenderfinder_agent2.py` is byte-identical to HEAD
  and remains isolated from `keywords.xlsx`.

## 1. State inventory and diagnostic reconciliation

The work began from a clean `main` at commit `1f649d1`. The original diagnosis
was confirmed: the live collection path scored against the editable workbook,
but replayed rows could carry stored keyword-derived values forward. The fix is
the unified normalization/rescore stage in
`01 Code/CONNECTOR_SWEEP/tenderfinder_demo_three_buckets.py:1169-1320`.
Persisted raw Vancouver scoring text is created in
`01 Code/CONNECTOR_SWEEP/tenderfinder_raw_sweep.py:729-740` and `:1958-2029`.

Task-generated run output was kept under `C:\tenderfinder_out`; no raw run,
mailbox, database, cache, virtualenv, or user state was added to the repository.
The repository `.gitignore` covers runtime paths and
`config/keywords_validation_last.txt`.

The targeted review and finding-by-finding resolutions are in
`06 QA/CODEX_REVIEW_1f649d1.md`.

## 2. Keyword-derived fields and the unified rescore decision

Every row entering the run working set now passes through the same current-rule
evaluation before downstream routing.

| Derived state | Recomputed from current workbook | Result |
|---|---:|---|
| Fit/current score and raw pre-cap score | Yes | Stored score is replaced |
| Positive/negative/geography/client matches | Yes | Match attribution refreshed |
| Civil include/exclude gate | Yes | Civil relevance refreshed |
| Tender-match classification | Yes | Classification refreshed |
| Civil label | Yes | Label refreshed |
| Vancouver tier and source-specific route | Yes, when raw scoring snapshot exists | Tier/route refreshed |
| Final bucket and signal quality | Yes | Downstream route uses fresh state |

The one explicit exception is an old Vancouver row without its raw scoring-text
snapshot. The program does not invent missing history: it keeps the stored
source-specific tier and records
`legacy_vancouver_scoring_text_unavailable` in the audit. New rows persist the
snapshot, so this exception does not apply to newly collected data.

Interaction decisions:

- A score drop does not silently delete a replayed row. The current route and
  before/after state are exposed in `Keyword_Change_Audit`.
- `Future_Projects`, `Outreach_Tracker`, and audit rows are keyed by stable ID;
  manual `Assigned To`, `Status`, and `Notes` are carried forward
  (`tenderfinder_demo_three_buckets.py:6535-6575`, `:6775-6825`).
- `Weekly_Review_Log` is cloned from the previous user master
  (`tenderfinder_demo_three_buckets.py:6579-6590`, `:7235-7237`).
- Technical and founder-facing audit layouts are both read correctly
  (`tenderfinder_demo_three_buckets.py:5557-5575`).

## 3. New baseline and historical stored values

The post-rescore offline baseline was run twice. Both projections contained 18
rows and were identical, with no count changes:

`C:\tenderfinder_out\keywords_e2e\baseline_post_idempotence.json`

The old stored values came from the earlier scoring context and are no longer a
golden contract. Current rules produced these six record-level changes (the
same values were consistently reflected across the three user-facing sheets):

| Lead ID | Stored score | Current-rule score | Other visible change |
|---|---:|---:|---|
| `5cebeefefcccf89e` | 74 | 80 | none |
| `83f5bf9ae4e00fec` | 78 | 80 | none |
| `85b8c63a5407e89b` | 86 | 100 | cap applied |
| `8d3867694e1fa9e0` | 65 | 89 | none |
| `97525eaf3f9face7` | 72 | 71 | none |
| `ac9206462d1ce7a5` | 81 | 53 | signal quality HIGH to MEDIUM |

Evidence and rule attribution:

- `C:\tenderfinder_out\keywords_e2e\baseline_old_vs_post.json`
- `C:\tenderfinder_out\keywords_e2e\baseline_post_attribution.json`
- `C:\tenderfinder_out\keywords_e2e\baseline_attribution.json`

The final user-master validator passed with nine visible tabs, matching
Dashboard recounts, no fixture leakage, Outreach traceability, preserved Weekly
Review Log, and an untouched prior master.

## 4. End-to-end matrix

| Check | Result | Black-box evidence |
|---|---|---|
| Baseline repeat | PASS | 18 records; identical projections and counts |
| Variant A | PASS | `5cebeefefcccf89e` 80 to 53; only that lead changed on three sheets; counts unchanged |
| Real collection path | PASS | injected records traversed raw normalization and user-master build, not direct scorer calls |
| Variant B contains | PASS | `e29de540ae0d4e76` raw 35 to 56, exact +21; only matching record became eligible |
| Variant B2 exact | PASS | same record raw 35 to 52, exact +17; partial-title record unchanged |
| Variant C1 | PASS | return code 2; clear missing `company_name`; no final files |
| Variant C2 | PASS | return code 0; structurally valid zero-user-record output; no hardcoded resurrection |
| Variant D1 | PASS | duplicate pair rejected with sheet and row |
| Variant D2 | PASS | invalid `fuzzy` match type rejected with sheet and row |
| Variant D3 | PASS | nonnumeric `high` weight rejected with sheet and row |
| Variant D4 | PASS | missing `category` column rejected |
| Variant E | EVIDENCE-BASED SKIP | no `gate_exclude` rule fired on the packaged offline sample |
| Cache matrix | PASS | stable same-process cache; fresh process and GUI forced reload picked up edits |
| Agent2 isolation | PASS | static only; no import or live execution |

Malformed-config messages were:

1. `Sheet Keywords row 229: duplicate (keyword, category) pair 'subdivision', 'positive'`
2. `Sheet Keywords row 2: match_type must be one of contains, exact, regex`
3. `Sheet Keywords row 2: weight 'high' is not a number`
4. `Sheet Keywords: missing column(s): category`

Variant evidence remains under `C:\tenderfinder_out\keywords_e2e`.

## 5. Manual-state and visible-audit proof

For persisted lead `ac9206462d1ce7a5`, a temporary current-rule edit changed
score/bucket `53/Future_Projects` to `44/Run_Queue`, and restoring the rule
changed it back to `53/Future_Projects`. In both runs:

- Assigned To remained `Founder`;
- Status remained `In Progress`;
- Notes remained `Manual triage must survive RESCORE_ALWAYS and bucket changes.`;
- Weekly Review Log remained present;
- exactly one keyword-change audit row was emitted per run.

Evidence:
`C:\tenderfinder_out\standalone_release_proof\persisted_rescore_manual_proof.json`.

A real Surrey record independently changed 52 to 43 when the `civil` positive
and include rules were disabled, changed Civil Relevant to Not Civil, then
returned to 52 after restoration. The canonical workbook hash did not change.
Evidence:
`C:\tenderfinder_out\standalone_release_proof\real_record_keyword_proof.json`.

## 6. Source registry and controlled live proof

`config/sources.csv` validates as 39 active sources: 21 tender and 18
development. Atomic CRUD and enable/disable logic is in
`01 Code/CONNECTOR_SWEEP/tenderfinder_source_registry.py:230-280`; the GUI
controls are in `tenderfinder_launcher_gui.py:881-927`; source tests use the
display-independent engine in `tenderfinder_engine.py:574-660`.

The extension proof added a disabled public RSS source, edited it, enabled it,
parsed one civil fixture record offline, disabled it, and restored the
canonical registry byte-for-byte. Evidence:
`C:\tenderfinder_out\standalone_release_proof\source_extension_proof.json`.

The controlled live gate made one GET to the public City of Surrey listing on
2026-07-14. It returned HTTP 200, required no login, used no retry or bypass,
and produced 43 raw / 25 normalized records, including two civil-relevant
records. Evidence:
`C:\tenderfinder_out\standalone_release_proof\surrey_live_proof.json`.

## 7. Windows GUI black-box verification

The repo-root launcher was opened through Windows File Explorer, matching a
founder's double-click path. The GUI visibly exposed Live Run, Offline/Test
Run, Validate Keywords, and Run Self-Test. The Source Checks tab visibly
showed the canonical 39-row registry and Add Source, Edit Source,
Enable/Disable, Validate Registry, Test Selected Offline, and Test Selected
Live controls.

GUI registry validation reported:

`Total 39 | Active 39 | Tender 21 | Development 18`.

GUI Self-Test then ran the shared engine offline in isolated state and
reported:

`Self-Test PASS | passed 7 | failed 0 | skipped 0 | intentionally excluded 4`.

Manifest:
`C:\tenderfinder_out\self_test\self_test_20260714_223610_9d8d8acc\run_manifest.json`.

Screenshots:

- `C:\tenderfinder_out\standalone_release_proof\gui_source_manager.png`
- `C:\tenderfinder_out\standalone_release_proof\gui_self_test_pass_main.png`
- `C:\tenderfinder_out\standalone_release_proof\gui_self_test_pass_dialog.png`

The window was closed normally and no TENDER_FINDER GUI remained open.

## 8. Test suite and honest exclusions

Final shared Self-Test: **7 passed, 0 failed, 0 skipped, 4 intentionally
excluded**, return code 0. Its seven checks include 12 keyword-loader checks,
6 standalone trust safeguards, 21 routing/gate checks, Outreach persistence,
review-workbook discovery, tender-signal routing, and the complete offline
pipeline.

The final user-facing `verify_package.bat` invocation also returned
`VERIFY_PACKAGE: PASS`; its manifest is
`C:\tenderfinder_out\self_test\self_test_20260714_224139_c6821098\run_manifest.json`.

The four exclusions are explicit rather than counted as PASS:

- live-source isolation (covered separately by the controlled Surrey gate);
- one stale legacy Surrey clock assertion;
- optional legacy `.eml` fixture checks whose mailbox payloads are absent from
  this sanitized repository;
- live execution of frozen `tenderfinder_agent2.py`.

An extended 22-script safe offline pass produced 19 successes and the same
three optional `.eml`-payload absences. These are pre-existing legacy fixture
gaps, not product data-integrity failures; no email payload was fabricated or
committed. No new failure was introduced.

## 9. Integrity closeout

| Artifact | SHA-256 / state |
|---|---|
| `config/keywords.xlsx` | `ea7e98097552d099f719b5a54b131386ed37a6202df3b904e07744aa11df429a` |
| `config/keywords_template.xlsx` | `7684a58bb2214b040067196e9509fe5155622f95baf1cf50c099ca10d5c0420c` |
| `config/sources.csv` | `5e7d251013f6a0256bc06bcdb17785d473a289bba4777d3268c0af2ce0b85108` |
| `01 Code/tenderfinder_agent2.py` | SHA-256 `5042fae15f64ce3acf822f538749f67f2b2569e16c13e6b251c8434be9d97137`; Git blob `2fd896b7e4ecdbd9a1059630aa57e432c0973aab`, identical to HEAD |

Runtime state resolves below `C:\tenderfinder_out`; package-local state roots
are rejected. The keyword override environment variable is required to be
unset by the final gate. The one ignored fixture `raw_runs` log created during
verification was identified as task-generated and removed. Repository diff,
cache/artifact, secret, and staging checks are performed immediately before
the release commit.

## 10. Git closeout

This report is included in the gated release commit. Because a file cannot
contain the hash of the commit that contains itself, the exact release commit
hash and confirmed `origin/main` push result are returned in the Codex final
response. The gate permits only a normal fetch/commit/push: no force, pull,
rebase, amend, reset, or history rewrite.

## Known non-blocking limitations and founder TODOs

- A disabled `custom` source draft needs an implemented adapter before it can
  be enabled; validation reports that honestly.
- Historical Vancouver rows without raw scoring text retain their stored
  source tier with the explicit legacy exception noted above.
- Keep `tenderfinder_agent2.py` frozen unless a separate migration is approved.
- An independent Claude review may be performed later as optional additional
  assurance; it does not affect this release.
- Founder habit: edit `config/keywords.xlsx`, save it, click **Validate
  Keywords**, then run. The next run reevaluates all available old and new
  records against the current file.
