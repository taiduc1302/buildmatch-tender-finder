# Patch 5.8 Backlog

## BC Bid Browser-Checked Public Browse

- Problem: BC Bid public browse URL resolves to a browser-check/reCAPTCHA page for automation.
- Location: `01 Code/CONNECTOR_SWEEP/tenderfinder_demo_three_buckets.py`, `sweep_bc_bid_public`.
- Correct fix: inspect BC Bid public UI network calls in a real browser session and identify a compliant public API/feed, or build a manual-review/export workflow.
- Why out of scope: authenticated/API decisions require legal/ToS review and must not be improvised.

## Surrey Development Applications V2

- Problem: a correct Surrey development-application FeatureServer layer was not found in the Patch 5.7 time box.
- Location: docs research in `docs/SURREY_DEVAPPS_RESEARCH.md`.
- Correct fix: use browser-based ArcGIS Hub inspection to locate a verified application-level dataset.
- Why out of scope: replacing connector routing could affect Track A counts.

## Long Preflight Regression

- Problem: fresh regression long preflight exited 2 and missed several source-register output files.
- Location: `01 Code/CONNECTOR_SWEEP/tests/run_regression.py` long output path preflight.
- Correct fix: audit safe-writer/temp redirect behavior for extremely long paths.
- Why out of scope: failure was present before Patch 5.7 changes and touches shared regression/safe-writer behavior.
