# Keywords, RESCORE_ALWAYS, and manual-field evidence

## Canonical workbook

- Path: `config/keywords.xlsx`.
- Validation: VALID; canonical workbook is the effective rules source.
- Active rules: 227.
- Inactive rules: 0.
- Categories: 12.
- Counts: known clients 19, collision protection 2, exclusion gate 28, civil
  include gate 51, weak terms 3, geography 4, civil labels 16, negative fit
  15, positive fit 30, tender language 18, Vancouver primary signals 26, and
  Vancouver secondary signals 15.
- External verified last-known-good snapshot: ready.
- SHA-256:
  `ea7e98097552d099f719b5a54b131386ed37a6202df3b904e07744aa11df429a`.

Invalid canonical configuration is a visible hard error unless the verified
external LKG is available. A custom path never silently falls back. GUI
Validate and Reload force a fresh load; cache behavior is explicit and tested.

## RESCORE_ALWAYS mutation proof

The E2E test copied the canonical workbook to a temporary directory, disabled
one active rule in that copy, reloaded it, and proved:

- score `52 -> 43`;
- tier `MEDIUM -> LOW`;
- bucket `Future_Projects -> Run_Queue`;
- hold reason `rescore_fit_below_50`;
- the same old/new values were written visibly to `Keyword_Change_Audit`.

The temporary copy was restored and the canonical workbook remained
byte-for-byte unchanged (`tests/test_rescore_always_e2e.py:71-152`).

## Founder-owned data

Multi-run tests prove `Status`, `Notes`, `Assigned To`, Outreach follow-up
state, and `Weekly_Review_Log` survive rescoring and bucket moves. A record that
moves below the visible Future gate remains visible in `Keyword_Change_Audit`
with its manual fields. Vancouver records recompute when scoring text exists;
old rows without that evidence retain their stored tier and visibly carry
`legacy_vancouver_scoring_text_unavailable`.
