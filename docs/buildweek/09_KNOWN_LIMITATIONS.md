# Known Limitations (truthful)

## Verified externally-only

- **On-screen GUI rendering** — the CI environment is headless Linux without
  tkinter, so the 7 widget-rendering tests are skipped there (with a justified
  reason) and verified on Windows. All GUI business logic is covered headlessly.
- **Live public-network refresh** — `Refresh Development Data` performs bounded,
  guarded live acquisition and is exercised in live mode / the controlled live
  proof, not in offline CI. The orchestration around it is fully tested with
  injected fakes.
- **Live OpenAI analysis** — requires a user-owned `OPENAI_API_KEY`. The SDK
  boundary is mocked in CI; a live smoke test is opt-in
  (`TENDER_FINDER_RUN_LIVE_OPENAI=1`). No model is claimed available without a
  real successful call.

## Product scope

- "Refresh Development Data" now runs a **real full paginated sweep**
  (`full_sweep_development_acquirer` → `tenderfinder_raw_sweep.run_connector`),
  not a bounded preview — proven against 8 real public sources (1,209-1,439
  records). `diagnostic_preview_acquirer` (the old bounded ~5-record sample)
  is retained only for source-health/diagnostic checks, not the production
  refresh path. See `docs/buildweek/final/01_FULL_RAW_SWEEP_IMPLEMENTATION.md`.
- The GUI's **Ranked Opportunities** tab lets the user select a specific
  opportunity from a real table (`ttk.Treeview`); "Analyze Selected
  Opportunity with AI" only analyzes that selection and is disabled until one
  is made. A separate, explicitly-labelled "Analyze Top-Ranked Opportunity"
  remains as a convenience shortcut. There is no filtering/search on the
  table yet (an intentional, documented scope limit, not a defect).
- Vancouver rezoning and development-permit sources remain `needs_configuration`
  until an official stable public endpoint is identified and safely tested; they
  are never selected by default and never shown as healthy.
- BC Housing / BC Builds are out of scope unless a safe official public source
  exists.
- The development-refresh dataset does not yet carry a manual-field concept
  (Assigned To / Notes / manual status) that survives across refreshes — each
  successful refresh replaces the active dataset outright. This is separate
  from, and does not affect, the original tender-focused pipeline's existing
  manual-triage preservation (`Assigned To`/`Status`/`Notes` surviving reruns),
  which remains intact and tested.

## What this product does NOT do

No continuous 24/7 harvesting, hosted SaaS, complete BC coverage, guaranteed
source uptime, automatic eligibility determination, replacement of estimator
judgment, production CRM/database/auth/multi-tenancy, or native HeavyBid /
Bluebeam / Screen2XYZ integration. AI output is advisory and evidence-referenced;
it never invents facts and never overrides the deterministic score.
