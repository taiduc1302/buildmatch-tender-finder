# PACKAGE MANIFEST

This file is replaced with a package-specific manifest during portable ZIP build and verification.

- Patch version: 5.23
- Status: template in working repo
- Notes: see the final packaged manifest for exact ZIP hash, commands run, and clean-unzip verification details.

## Configurable company-profile layer

- `config/keywords.xlsx` — live pre-filled configuration.
- `config/keywords_template.xlsx` — blank founder/customer handoff template.
- `01 Code/CONNECTOR_SWEEP/tenderfinder_keywords_config.py` — shared strict loader.
- `01 Code/CONNECTOR_SWEEP/tests/test_keywords_config.py` — offline loader/GUI/scoring checks.
- `01 Code/CONNECTOR_SWEEP/tests/keywords_golden_snapshot.py` — timestamp-free golden comparison helper.
- `docs/KEYWORDS_CONFIG_DECISIONS.md` — schema and compatibility decisions.
- `AGENTS.md` — standing repository rules for future agents.

## Most recent authoritative packaged manifest

- `latest_verified_output/demo_p522/PACKAGE_MANIFEST.md` (Patch 5.22, commit `7944908d3a129da867120cfdc108b872bb2e4aab`) is
  the newest verified, evidence-backed manifest as of this repair pass. It documents the actual packaged build
  (ZIP hash, commands run, test results) that `latest_verified_output/demo_p522/` corresponds to.
- This root-level file stays a template; do not treat it as authoritative build evidence by itself.
