# Codex targeted review — commit `1f649d1` and current stabilization code

Date: 2026-07-15 (America/Vancouver)

Reviewer: Codex

Baseline commit under review: `1f649d1f275a91e42ce36cbdf9b8c7997c1e8926`

Current stabilization baseline: `1780ad6a112dd7ca398d705b1f8ffb348e7aaf6a`

## Review outcome

**PASS — Codex targeted review completed and all blocking/high findings resolved.**

The required review gate is this Codex review. An external Claude review is an
optional future additional audit and is not required for this release. No
blocking or high-severity finding from the targeted review remains open.

## Required targeted areas

### Editable regex safety — PASS

The workbook accepts `contains` and `regex` rules, but editable regex is not
allowed to fall back to an unbounded standard-library execution path. Patterns
are limited to 256 characters, scoring text to 100,000 characters, and each
search to 0.02 seconds. Backreferences, lookarounds, conditional groups, and
nested unbounded quantifiers are rejected before use
(`01 Code/CONNECTOR_SWEEP/tenderfinder_keywords_config.py:90-106`,
`:347-375`). Missing bounded-regex support is a hard validation error, not a
silent fallback (`:359-363`).

The focused keyword suite covers invalid/unsafe expressions and explicit cache
reload behavior (`tests/test_keywords_config.py:136-188`, `:251-268`). The
authoritative Self-Test reports the keyword suite `13 passed / 0 failed`.

### `RESCORE_ALWAYS` — PASS

Every normalized replayed record is evaluated using the currently loaded
keyword configuration. The E2E mutation test edits only a temporary copy of
`keywords.xlsx`, disables the `earthwork` rule, and proves this visible change:

- score `52 -> 43`;
- tier `MEDIUM -> LOW`;
- bucket `Future_Projects -> Run_Queue`;
- hold reason `rescore_fit_below_50`;
- matching old/new values in `Keyword_Change_Audit`.

The temporary workbook is restored and the canonical workbook SHA remains
unchanged (`tests/test_rescore_always_e2e.py:71-152`). The authoritative
Self-Test includes this E2E check and reports it PASS.

### Manual `Status` / `Notes` / `Assigned To` and review history — PASS

Prior founder-owned values are indexed by stable ID and restored into the
current `Future_Projects`, `Outreach_Tracker`, and visible keyword audit rows
(`tenderfinder_demo_three_buckets.py:6526-6662`, `:6767-6920`). The two
intentional `Keyword_Change_Audit` header layouts are detected separately
(`:5651-5658`). `Weekly_Review_Log` is cloned from the prior user master rather
than reset from the template (`:6664-6674`, `:7320-7323`).

The multi-run safeguard proves the manual fields and weekly log survive a
keyword-driven move (`tests/test_standalone_weekly_release.py:302-379`). The
separate Outreach persistence check also passes.

### Cache isolation and reload semantics — PASS

The keyword cache key includes workbook path, external settings path, and LKG
policy. Normal same-process reads are stable; `force_reload=True` evicts only
that key and reloads the workbook (`tenderfinder_keywords_config.py:689-725`).
Engine preflight and GUI Validate/Reload use forced reload at run boundaries.
Last-known-good snapshots and validation reports live under the external state
root, not beside the workbook. Coverage is in
`tests/test_keywords_config.py:205-285`.

### Vancouver tier contradictions — PASS with one explicit legacy exception

New development records persist bounded `keyword_scoring_text`
(`tenderfinder_raw_sweep.py:798`, `:2054`). Replays with that evidence recompute
score, Vancouver tier, and route. Historical records without a scoring-text
snapshot retain the previously stored source-specific tier and are visibly
marked `legacy_vancouver_scoring_text_unavailable`; the program does not invent
missing evidence (`tenderfinder_demo_three_buckets.py:1188-1204`). Both paths
are covered by `tests/test_standalone_weekly_release.py:272-301`.

### `tenderfinder_agent2.py` isolation — PASS

The frozen legacy program is not imported by the GUI or engine and does not
consume the active keyword loader. Static isolation assertions are in
`tests/test_standalone_weekly_release.py:380-399`. Its SHA-256 before and after
Self-Test is unchanged:
`5042fae15f64ce3acf822f538749f67f2b2569e16c13e6b251c8434be9d97137`.

## Additional material findings discovered during this review

### [RESOLVED BLOCKING] Editable network destinations and redirects were unsafe

A centralized fail-closed public-network policy now validates supported
HTTP(S) syntax, resolves hosts, rejects any non-public address, disables
automatic redirects, validates every redirect hop, and blocks private
Playwright subrequests (`tenderfinder_url_safety.py:27-60`, `:153-228`,
`:234-310`). Certificate verification is not weakened. Security tests cover
private IPv4/IPv6, localhost, DNS failure, malformed schemes, requests and
urllib redirects, and browser subrequests
(`tests/test_stabilization_security.py:133-367`). Result: `11/11 PASS`.

### [RESOLVED HIGH] Live tests could overstate thin or irrelevant samples

Development live PASS now requires successful transport, normalized records
with meaningful project detail, and at least one current HIGH/MEDIUM record.
HTTP 200 plus thin/all-LOW rows returns `LIVE SOURCE REVIEW REQUIRED`, not PASS
(`tenderfinder_engine.py:1132-1210`, `:1367-1400`). Regression tests are at
`tests/test_source_registry_stabilization.py:253-307`.

The first Surrey probe returned old concluded rows, exposing a sampling defect.
The registry now supports validated `test_query_where` and
`test_query_order_by` controls (`tenderfinder_source_registry.py:41-42`,
`:259-273`). The bounded request asks ArcGIS for exactly five rows; it does not
download a larger page and slice locally. Surrey's controlled sample then
produced five normalized records, four current HIGH/MEDIUM records, and a
truthful `verified_live` classification. Abbotsford returned five thin LOW
records and correctly remained `ready_for_live_test`.

### [RESOLVED HIGH] Live-test query URL could replace the reusable endpoint

The auditable final request URL and reusable base endpoint are now separate.
Only the base `resolved_endpoint` may populate `last_good_endpoint`; the query
URL remains `final_validated_url` in evidence (`tenderfinder_engine.py:1402-1435`).
The regression is covered by
`tests/test_source_registry_stabilization.py:309-344`.

### [RESOLVED HIGH] Source registry status and edit durability were misleading

`config/sources.csv` is the single runtime registry. Enabled, runtime-eligible,
fixture-tested, live-verified, manual, blocked, wrong-source, and deprecated are
separate concepts (`tenderfinder_source_registry.py:53-70`, `:277-289`,
`:417-431`). Writes validate the complete registry, preserve unknown columns,
flush and fsync, create an external timestamped backup, then atomically replace
the canonical file (`:442-488`). Configuration validation, offline parser
testing, and explicit live testing are separate operations. Source-registry
suite result: `11/11 PASS`.

### [RESOLVED MEDIUM] Offline parser UI could say the parser was not used

Adapter tests now populate `parser_used`, parser name, candidate counts, and
normalization details. The GUI displays `Parser used: YES (<parser>)` after an
actual fixture parse. This was verified in the moved release candidate and is
captured in `06 QA/RELEASE_EVIDENCE_INTERNAL_BETA_V1/screenshots/`.

### [RESOLVED HIGH] Clean release omitted compatibility launchers

The first extracted-package GUI Self-Test truthfully failed because the package
test allowlist included launcher-consistency checks but omitted
`run_tenderfinder_demo.bat` and `run_tenderfinder_demo_fast.bat`. Both files are
now included by the deterministic release builder. The moved package GUI
Self-Test subsequently passed `110 / 0 / 1 / 4 / 0` (pass/fail/skip/excluded/no
fixture).

### [RESOLVED HIGH] Fresh setup emitted misleading path errors

The original shortcut-generation block produced ten `The system cannot find
the path specified` messages despite exit 0. Setup now discovers the real
Windows Desktop, calls a PowerShell shortcut subroutine outside the CMD block,
preserves the repository-relative canonical launcher, and propagates failures.
A fresh extract created a new `.venv`, installed the full dependency set and
Chromium, created a shortcut to the canonical launcher, moved the installed
folder, reused its environment, and recreated a working moved-path shortcut.
Launcher portability suite result: `5/5 PASS`.

### [RESOLVED HIGH] A run could select another installation's master template

The full pre-commit Self-Test exposed this through its own log: the checkout
selected a newer copied template from the moved test package under
`C:\tenderfinder_out` instead of its own `00 Master` template. No user data was
changed, but this was an unsafe cross-install dependency. Master discovery now
uses a valid template within the current package before considering any
external fallback (`tenderfinder_demo_three_buckets.py:5363-5439`). A
regression creates an older local template and a newer foreign-install
template and proves the current package still wins
(`tests/test_standalone_weekly_release.py:403-435`). The repeated full
Self-Test selected
`C:\Projects\buildmatch-tender-finder\00 Master\TENDER_FINDER_Tender_Intelligence_Working_Master_TEMPLATE_v1.xlsx`.

## Current verification snapshot

- Authoritative checkout Self-Test: **PASS**, `112 passed / 0 failed / 2
  skipped / 3 intentionally excluded / 0 not tested due to fixture`, exit 0.
- Self-Test network guard: zero network attempts; real pipeline executed with
  `--no-fetch`.
- Manifest:
  `C:\tenderfinder_out\self_test\self_test_20260715_100508_12831ed5\run_manifest.json`.
- Moved extracted package GUI Self-Test: **PASS**, `110 / 0 / 1 / 4 / 0`, exit
  0. The extra package exclusion records that an archive has no Git checkout.
- Canonical `keywords.xlsx`: VALID, 227 active, 0 inactive, 12 categories;
  SHA-256 `ea7e98097552d099f719b5a54b131386ed37a6202df3b904e07744aa11df429a`.
- Canonical `sources.csv`: 39 configured, 39 enabled, 27 runtime-eligible, 1
  verified live, 26 ready for live test, 4 manual, 3 need configuration, 1
  blocked, 4 wrong-source; SHA-256
  `1901c7cc73e8e240d74d8e534924c7b814f5ad32b68ee442faa52138f40f0306`.
- Canonical launcher SHA-256:
  `ef9176ae45313e90858f9430eea11106e7062c35b7c9abf36070311a04206371`.
- Windows GUI black-box: double-click shortcut launch, Offline/Test Run,
  Keywords validation/reload status, Source Manager, parser test, Add Source
  form, and GUI Self-Test were exercised successfully.

## Remaining non-blocking limitations

- Only Surrey has current controlled `verified_live` evidence. Abbotsford was
  tested but correctly requires adapter/source review; the other 37 configured
  sources were not live-tested in this release.
- Some configured sources have adapter-level fixtures rather than
  source-specific fixtures.
- Python and first-run dependency installation are prerequisites; this is a
  portable source package, not a self-contained `.exe`.
- The engine contract is a future BuildMatch integration seam, not an existing
  BuildMatch API or deployed integration.
