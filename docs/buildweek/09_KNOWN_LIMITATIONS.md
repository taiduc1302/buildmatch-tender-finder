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

- The GUI's "select a ranked opportunity" analyzes the **top-ranked** record of
  the active dataset. A full in-GUI results grid with per-row selection is not
  built (an intentional non-goal for the competition).
- `default_development_acquirer` returns a **bounded normalized sample** per
  source (via the guarded live source test), sufficient for the demo and honest
  about provenance; it is not a full production harvest.
- Vancouver rezoning and development-permit sources remain `needs_configuration`
  until an official stable public endpoint is identified and safely tested; they
  are never selected by default and never shown as healthy.
- BC Housing / BC Builds are out of scope unless a safe official public source
  exists.

## What this product does NOT do

No continuous 24/7 harvesting, hosted SaaS, complete BC coverage, guaranteed
source uptime, automatic eligibility determination, replacement of estimator
judgment, production CRM/database/auth/multi-tenancy, or native HeavyBid /
Bluebeam / Screen2XYZ integration. AI output is advisory and evidence-referenced;
it never invents facts and never overrides the deterministic score.
