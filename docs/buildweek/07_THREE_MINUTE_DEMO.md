# Three-Minute Demo (Public Snapshot mode)

The default demo runs against the committed, sanitized **Public Snapshot** so it
never depends on live sites during a presentation.

## Setup (once)

```powershell
# Promote the public snapshot as the active dataset.
python -c "import sys; sys.path.insert(0, r'01 Code\CONNECTOR_SWEEP'); import tenderfinder_snapshot as s; print(s.promote_snapshot(root='.'))"
```

## Script

1. **The problem** — construction estimators drown in scattered public
   opportunities; most are not a fit.
2. **Profile selection** — choose a contractor profile (Civil / Multi-Family
   Residential / General Contractor) in the Run tab.
3. **Provenance** — the banner reads `PUBLIC SNAPSHOT — captured July 19, 2026`,
   with source provenance (Surrey / Maple Ridge / Township of Langley feeds).
4. **Truthful counts** — 8 captured records; 6 score ≥ 60 under the Civil preset.
5. **Deterministic ranking** — the list ranks watermain/servicing/subdivision
   opportunities at the top (fit 100) and the interior tenant-improvement and
   sign-permit records at the bottom (fit 0 / 32).
6. **Select an opportunity** — the top-ranked record (SNAP-001, Fraser Highway
   subdivision servicing).
7. **OpenAI analysis** — click **Analyze Selected Opportunity with AI**.
8. **Evidence** — the AI shows evidence-backed positive and negative factors
   (each citing a public field), separate from the deterministic fit/bucket.
9. **Uncertainties & gaps** — eligibility uncertainties and missing information
   are listed; the deterministic score is unchanged.
10. **Estimator next step** — export the combined analysis (JSON/Markdown) for
    the estimator's review.

## What NOT to claim during the demo

No continuous 24/7 harvesting, no hosted SaaS, no complete BC coverage, no
guaranteed source uptime, no automatic eligibility determination, no replacement
of estimator judgment, no production CRM, and no native HeavyBid/Bluebeam/Screen2XYZ
integration. AI output is advisory and evidence-referenced, not authoritative.
