# Claims Ledger (OpenAI Build Week 2026 §24)

Per the official rules' required format. `UNKNOWN` means evidence is not yet
available to this session — it is not a placeholder for "assume true."

| Claim | Evidence | Status |
|---|---|---|
| Project works end-to-end (deterministic scoring, ranking, export) | 216-222 passed tests (Linux + real tkinter/X11), real controlled live sweep against 8 public sources, real Windows CI green — see `07_REMOTE_PR_AUDIT.md`, `03_CONTROLLED_LIVE_REFRESH_RESULTS.md` | PASS |
| Codex built the majority of the project's core functionality | Founder states the original scraper (connector sweep, engine, scoring, GUI shell) was built in a Codex/GPT-5.6 session on/around 2026-07-14, shared at `https://chatgpt.com/share/e/6a5e47aa-2eac-83e8-8a55-41ba5b3a7694`. This session could not fetch that link (blocked to automated access) and cannot independently verify its content or extract the `/feedback` Session ID | UNKNOWN |
| GPT-5.6 was meaningfully used | Founder-asserted as part of the same Codex session above; not independently verified by this session | UNKNOWN |
| `/feedback` Codex Session ID obtained and recorded | Not yet retrieved by the founder | UNKNOWN |
| Claude Code's role is disclosed, not concealed | `README.md` "AI tool and contributor disclosure" section, this document, and `docs/buildweek/final/*` all name Claude Code's actual contributions | PASS |
| Data is synthetic for the public demo | Public Snapshot (`demo_data/public_snapshot`) is 82 **real**, sanitized, public-source municipal records, not synthetic — this is public open data (not employer/client data) but differs from the pack's stricter internal preference for synthetic demo data. Founder decision pending: keep as real-public (transparent) or regenerate as fully synthetic | UNKNOWN — founder decision required |
| Repository is public-safe (no employer branding, secrets, PII) | A real employer name was found in 6 tracked files, 2 workbook fixtures, and 2 committed screenshots; replaced with fictional "Meridian Civil Works" and re-verified via a name-specific grep sweep (zero hits) and `package_audit.py --mode repo .` (PASS) this session | PASS (after this session's remediation) |
| Demo is reproducible offline | Public Snapshot + Self-Test run fully offline, no live-network dependency for judging | PASS |
| Live OpenAI analysis call verified | No `OPENAI_API_KEY` available in any session to date; full mocked test suite (23 tests) covers every code path except the live network call | UNKNOWN (external blocker, documented in `04_LIVE_OPENAI_RESULTS.md`) |
