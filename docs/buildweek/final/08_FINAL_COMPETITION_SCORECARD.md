# Final Competition Readiness Scorecard

> AI-tool attribution note: this document describes work done by Claude Code during this session. For the full, honest Codex/GPT-5.6/Claude Code contribution breakdown required by the OpenAI Build Week rules, see the README's "AI tool and contributor disclosure" section and `docs/buildweek/final/CLAIMS_LEDGER.md` — this document alone should not be read as claiming Claude Code built the project's core functionality.

Scores 0-10 with evidence, deductions, and confidence. Written after this
session's remediation and remote CI verification (see `07_REMOTE_PR_AUDIT.md`).

| Dimension | Score | Evidence | Deductions | Confidence |
|---|---|---|---|---|
| Problem clarity | 9 | Demo script (`07_THREE_MINUTE_DEMO.md`) states the problem in one line; the workflow (profile → refresh/snapshot → ranked list → select → AI → export) maps directly to an estimator's real triage process | -1: no user research/testimonial evidence, only internal reasoning | High |
| Originality | 7 | Deterministic-scoring-plus-advisory-AI split, with disagreement surfaced for human review rather than auto-applied, is a genuinely considered design, not a thin OpenAI wrapper | -2: the underlying municipal-open-data-aggregation idea is not novel; -1: no unique data source no competitor could replicate | Medium |
| Technical implementation | 8 | Real full-pagination sweep against 6 distinct fetch types (ArcGIS REST/Hub, Opendatasoft, PDF-table-extraction) proven live; strict-schema OpenAI integration; atomic dataset promotion with rollback; formula-injection and prompt-injection guards; a genuine concurrency race found and fixed | -1: manual-field preservation not yet extended to the new refresh path (documented limitation); -1: no filtering/search on the ranked table yet | High |
| Verified functionality | 8 | 216 offline tests + 199 Self-Test checks, ALL green; a real controlled sweep against 8 public sources verified end-to-end; Windows CI genuinely passed (after fixing a real Windows-only defect it caught) | -2: live OpenAI call unverified (no key available to this session) | High for everything except live OpenAI |
| OpenAI value | 7 | Evidence-referenced, schema-strict, disagreement-flagging, cached, prompt-injection-hardened — a serious integration, not a demo toy | -2: cannot confirm the live call actually produces good output without a real key; -1: the deterministic engine alone already ranks well, so AI's marginal value is "richer explanation" rather than "otherwise impossible" | Medium (capped by the untested live path) |
| Deterministic/AI architecture | 9 | Deterministic score/bucket/matched-terms are read-only inputs to the AI prompt; AI never mutates them; disagreement is a distinct, surfaced state (`HUMAN_REVIEW`), not silently resolved either way; tested | none significant | High |
| Development story (Claude Code) | 9 | Two full sessions: recovery from a non-existent prior commit, systematic gap-closing, and — the strongest evidence — a real controlled live sweep that found and fixed 5 genuine defects synthetic tests could not have caught, all documented with real logs, not asserted | -1: the story is not itself packaged into demo-ready narrative material (e.g. a slide) | High |
| Construction user value | 8 | Solves a real, named pain point (manual CLI + copy-paste for development-application review) with a one-click refresh, truthful metrics, and contractor-specific ranking (104 vs 246 vs 144 BID_LATER opportunities across presets on the same real data) | -2: no real estimator has used it; value is inferred, not observed | Medium |
| UX | 7 | Ranked Opportunities table, disabled-until-selected AI button, persistent data-mode banner — now backed by real screenshots of the actually-rendered app (`final/evidence/*.png`, real tkinter + X11, not a mockup), showing the banner, disabled state, a real 82-record load, and row #2 (not #1) selected with its own evidence and an enabled AI button | -1: real screenshots exist but on Linux/X11, not a real Windows desktop; -2: no filtering/search, no pagination for very large (1,000+ record) result sets | Medium (real rendering evidence exists; still no human interaction on real Windows) |
| Live data credibility | 8 | Real, reproducible controlled sweep against 6 named public BC municipal feeds, with per-source counts, HTTP statuses, and a genuine defect trail | -2: not a 24/7 continuously-updated dataset (by design, and correctly not claimed as one) | High |
| Demo reliability | 8 | Runs fully offline against 82 real records with no live-site dependency; fallback behaviour for a down source or unavailable OpenAI is documented | -2: never actually rehearsed by a human in front of an audience | Medium |
| Security | 8 | No secrets/PII in the snapshot (verified + tested), formula-injection guard applied to all new writers, prompt-injection hardening, API key never logged/cached, safe-path enforcement, source-safety gating before any fetch | -2: no external/third-party penetration test; internal adversarial review only | Medium-high |
| Documentation | 9 | 21 Build Week docs (11 from the prior session + 10 `final/` docs this session), all reconciled against actual code behaviour, with stale claims found and corrected twice this session | -1: some docs slightly redundant across the two doc sets (historical vs. final) | High |
| Submission readiness | 7 | PR #3 open, mergeable, real CI green, no unresolved review comments, no secrets, no unrelated files | -2: two genuine external blockers (live OpenAI, interactive Windows) remain unresolved and require the founder's own credentials/machine; -1: not yet marked ready-for-review (deliberately left as the founder's decision) | High |

**Average: 8.0 / 10** (updated from 7.9 after the UX score moved 6→7 on real
rendering evidence; see `02_WINDOWS_ACCEPTANCE_RESULTS.md`)

## Final recommendation

**`SUBMIT ONLY AFTER REMAINING EXTERNAL CHECK`**

The product, architecture, and evidence trail are strong enough for
`SUBMIT AS PRIMARY PROJECT`, but two items genuinely require the founder
before that claim is honest:

1. A real live OpenAI call with the founder's own `OPENAI_API_KEY` — the
   entire "OpenAI value" and part of "verified functionality" scores are
   capped until this happens (5 minutes of work: set the key, run the opt-in
   smoke test in `docs/buildweek/final/04_LIVE_OPENAI_RESULTS.md`).
2. A human actually using the running GUI on real Windows — real screenshots
   now exist (`final/evidence/*.png`, captured via a genuine tkinter/X11
   render on Linux), so this is no longer "nobody has seen it render," but a
   human has still never clicked through it on the actual target OS
   (10-15 minutes: `Launch_TENDER_FINDER_GUI.bat`, walk the checklist in
   `docs/buildweek/08_WINDOWS_ACCEPTANCE.md`).

Both are fast, low-risk, and entirely within the founder's control. Once
done, this becomes `SUBMIT AS PRIMARY PROJECT` on the evidence already
gathered — nothing else in the implementation blocks that call.
