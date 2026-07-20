# First Full Product Audit (Phase 8)

> AI-tool attribution note: this document describes work done by Claude Code during this session. For the full, honest Codex/GPT-5.6/Claude Code contribution breakdown required by the OpenAI Build Week rules, see the README's "AI tool and contributor disclosure" section and `docs/buildweek/final/CLAIMS_LEDGER.md` — this document alone should not be read as claiming Claude Code built the project's core functionality.

Fresh, evidence-based audit against the original product goals, performed
after implementing the Phase 1-6 fixes and running a real controlled live
sweep. Classifications: VERIFIED OPERATIONAL / VERIFIED WITH LIMITATIONS /
IMPLEMENTED BUT NOT TESTED / PARTIALLY IMPLEMENTED / BROKEN / UNKNOWN.

## Core product

| Question | Classification | Evidence |
|---|---|---|
| Does the GUI run? | VERIFIED WITH LIMITATIONS | Windows CI (`windows-latest`, real tkinter) constructs the full app including the new Ranked Opportunities Treeview and passed after fixing a real Windows-only workbook-handle bug that first CI run caught (see `06_REMEDIATION_LOG.md` item 11); real screenshots (`final/evidence/*.png`) now show it actually rendering under Python 3.12 + real tkinter/X11 (Linux, not Windows), including a live 82-record load and a non-top-ranked row selection enabling the AI button — genuine additional evidence, though a human's interactive use on real Windows remains unverified |
| Does full refresh work? | VERIFIED OPERATIONAL | Real controlled sweep: 8/8 sources, 1,209-1,439 records across 3 runs |
| Does it retrieve full records? | VERIFIED OPERATIONAL | Real pagination confirmed (`[arcgis] batch=1 offset=0 fetched=200`), 1,209 normalized records, not a preview |
| Does scoring run automatically? | VERIFIED OPERATIONAL (fixed this session — was previously not wired) | Run 3: 104/531/574 bucket counts from real data |
| Are current-run metrics truthful? | VERIFIED OPERATIONAL (2 defects fixed this session) | `RunMetrics.is_reconciled() == True` on the real run; regression tests for both the thin-record and records_live-ordering bugs |
| Is data provenance visible? | VERIFIED OPERATIONAL | Data-mode banner in both the Run tab and the new Opportunities tab, driven by the same `current_data_mode_banner()` helper |
| Can the user choose a preset? | VERIFIED OPERATIONAL | 3 presets, materially different real-data results (104/246/144 BID_LATER) |
| Can the user select an opportunity? | VERIFIED OPERATIONAL (fixed this session — was previously auto-picked) | Ranked Opportunities tab + `resolve_selected_opportunity` never substitutes; 3 dedicated regression tests including one that explicitly proves a non-top-ranked selection is what gets analyzed |
| Does live OpenAI analysis work? | IMPLEMENTED BUT NOT TESTED (genuine external blocker) | No `OPENAI_API_KEY` in this environment; full mocked suite (23 tests) covers every code path except the real network call |
| Is AI evidence-based? | VERIFIED OPERATIONAL | Strict JSON-schema structured output, prompt-injection-hardened developer instruction, deterministic-authority + disagreement tests |
| Does export work? | VERIFIED OPERATIONAL | JSON + Markdown export tested |
| Does failure recovery work? | VERIFIED OPERATIONAL | Total-failure, validation-failure, and promotion-failure paths all preserve the previous dataset and mark it stale; tested + confirmed by the Run 1 real-world validation failure, which correctly retained the prior state |

## Competition value

| Question | Classification | Evidence |
|---|---|---|
| Is the problem understandable? | VERIFIED OPERATIONAL | Demo script in `docs/buildweek/07_THREE_MINUTE_DEMO.md` |
| Is the workflow coherent? | VERIFIED OPERATIONAL | Profile → refresh/snapshot → ranked list → select → AI → export, all wired end-to-end |
| Is OpenAI essential and meaningful? | VERIFIED WITH LIMITATIONS | The analysis is genuinely evidence-referenced and separate from the deterministic score (meaningful), but its live behaviour is unverified here (external blocker) |
| Is deterministic scoring preserved? | VERIFIED OPERATIONAL | AI never mutates fit score/matches/bucket; disagreement surfaced, not auto-applied |
| Is the three-minute demo reliable? | VERIFIED OPERATIONAL | Runs fully offline against the 82-record real Public Snapshot; no live-site dependency |
| Are claims truthful? | VERIFIED OPERATIONAL | No fabricated live-verification claims in this document set; genuine blockers are labelled as such, not glossed over |
| Is the product clearly better than the prior desktop beta? | VERIFIED OPERATIONAL | The prior beta required manual CLI + copy-paste for development data; this version has a one-click, auto-scored refresh with truthful metrics, presets, and an AI copilot — none of which existed before Build Week |

## Security

| Question | Classification | Evidence |
|---|---|---|
| No secrets | VERIFIED OPERATIONAL | `package_audit.py --mode repo .` PASS after every change |
| No private data | VERIFIED OPERATIONAL | Snapshot applicant names sanitized; `test_snapshot_is_sanitized` |
| Safe public-source access | VERIFIED OPERATIONAL | Only unauthenticated, public, non-login sources used; `source_readiness_errors` gate enforced before any fetch |
| Safe paths | VERIFIED OPERATIONAL | `test_never_writes_inside_package`; datasets always under the external state root |
| Formula-injection protection | VERIFIED OPERATIONAL (fixed this session — was previously missing on the new refresh-service writers) | `append_untrusted_row` now used everywhere untrusted public data is written to a workbook cell; 2 regression tests |
| Prompt-injection protection | VERIFIED OPERATIONAL | Developer instruction + dedicated test (`test_prompt_injection_content_is_treated_as_data`) |
| No API-key logging | VERIFIED OPERATIONAL | `test_api_key_never_in_cache_key`; key never written to manifests/logs/cache |
| Safe cache | VERIFIED OPERATIONAL | Cache key excludes the API key; invalidates on input change |
| No committed runtime state | VERIFIED OPERATIONAL | `.gitignore` excludes `tenderfinder_out/`; all state roots resolve outside the package (`resolve_state_root` raises `RuntimeStateError` if not) |

## Release

| Question | Classification | Evidence |
|---|---|---|
| Clean package | VERIFIED OPERATIONAL | `build_clean_release.py` PASS, 117 deterministic entries |
| Reproducible setup | VERIFIED OPERATIONAL | `requirements.txt` now correctly declares `openai` (fixed this session) |
| Windows startup | VERIFIED WITH LIMITATIONS (was UNKNOWN) | Real Windows CI passes; a real `pwsh` + tkinter/X11 run on Linux exercises the same headless-verifiable steps and produces the identical release SHA256 as the plain-Python run; the `.bat` launchers and a human's interactive startup on real Windows remain unverified — see `02_WINDOWS_ACCEPTANCE_RESULTS.md` |
| Documentation | VERIFIED OPERATIONAL | Stale claims (auto-pick AI, 8-record snapshot) corrected this session |
| Limitations | VERIFIED OPERATIONAL | `docs/buildweek/09_KNOWN_LIMITATIONS.md` + this document set are truthful about what remains unverified |
| PR state | VERIFIED OPERATIONAL | PR #3 open, draft, mergeable — see `07_REMOTE_PR_AUDIT.md` |
| CI | VERIFIED WITH LIMITATIONS | Prior push's CI passed; this session's changes pending a fresh run |
