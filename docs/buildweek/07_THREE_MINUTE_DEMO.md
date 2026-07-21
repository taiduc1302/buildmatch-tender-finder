# Three-Minute Demo (Public Snapshot mode)

> AI-tool attribution note: for the honest Codex/GPT-5.6/Claude Code
> contribution breakdown, see the README's "AI tool and contributor
> disclosure" section. This script below is a planning script only —
> recording, narrating, and uploading it is the founder's own action.

## Recommended timed structure (OpenAI Build Week video requirements)

The official rules require the video to explain both how Codex was used and
how GPT-5.6 was used, with audio narration, 3 minutes or less. Recommended
timing (a planning guideline, not an official requirement):

```text
0:00–0:15   Problem and hook
0:15–0:35   Product and user
0:35–1:35   Working end-to-end demo (steps 2-10 below)
1:35–2:00   GPT-5.6 role — what it analyzes (opportunity evidence -> structured,
            evidence-referenced recommendation), and that it is advisory only,
            never overriding the deterministic fit score
2:00–2:25   Codex role — name the original session
            (https://chatgpt.com/share/e/6a5e47aa-2eac-83e8-8a55-41ba5b3a7694)
            and what it built (the core scraper/engine/scoring baseline);
            state the Session ID once the founder has retrieved it
2:25–2:45   Impact and differentiation
2:45–2:55   Conclusion
```

A silent screen recording or a recording with only background music does not
satisfy the narration requirement — the video must have spoken audio.

The default demo runs against the committed, sanitized **Public Snapshot** so it
never depends on live sites during a presentation. The snapshot contains 82
real, sanitized public development-application records captured via a
controlled live sweep of six BC municipal open-data feeds — not fictitious
data (see `docs/buildweek/03_DATA_MODES_AND_METRICS.md` and
`demo_data/public_snapshot/generate_snapshot.py`).

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
   with source provenance (Surrey, Maple Ridge, Township of Langley, Coquitlam,
   and Vancouver open-data feeds).
4. **Truthful counts** — 82 captured records; 15 score ≥ 60 under the Civil
   preset.
5. **Deterministic ranking** — open the **Ranked Opportunities** tab; the list
   ranks real subdivision/rezoning/servicing applications at the top (e.g. a
   Surrey rezoning + road/drainage-network application, fit 71) and low-signal
   applications (e.g. a signage/minor permit) at the bottom.
6. **Select an opportunity** — click a specific row in the ranked table (not
   an auto-picked one). The **Analyze Selected Opportunity with AI** button
   enables only once a row is selected.
7. **OpenAI analysis** — click **Analyze Selected Opportunity with AI**.
8. **Evidence** — the AI shows evidence-backed positive and negative factors
   (each citing a public field), separate from the deterministic fit/bucket.
9. **Uncertainties & gaps** — eligibility uncertainties and missing information
   are listed; the deterministic score is unchanged.
10. **Estimator next step** — export the combined analysis (JSON/Markdown) for
    the estimator's review.
11. **Optional: Live Refresh** — briefly show **Refresh Development Data**
    against the same real public sources and the Source Checks tab's honest
    per-source health (Vancouver rezoning/development-permit sources correctly
    shown as `needs_configuration`, never selected or presented as healthy).

## What NOT to claim during the demo

No continuous 24/7 harvesting, no hosted SaaS, no complete BC coverage, no
guaranteed source uptime, no automatic eligibility determination, no replacement
of estimator judgment, no production CRM, and no native HeavyBid/Bluebeam/Screen2XYZ
integration. AI output is advisory and evidence-referenced, not authoritative.
