# FUTURE WEB / DESKTOP APP PLAN — Tender Finder

**In plain English:** today this tool is a set of scripts you run by hand that
produce an Excel file. This document describes how a developer could turn it
into a real app — first a simple desktop app, later a website multiple people
could log into. **None of this is built yet — it's a roadmap, not a promise,**
and every phase below requires a software developer to implement; a
non-technical reader mainly needs to know the rough shape (a few weeks for a
basic refactor, longer for a full multi-user website) when discussing
priorities or budget with a developer.

How to evolve this starter kit from a batch/Tkinter + Excel workflow into a
standalone desktop app and, later, a multi-user web platform. This is a plan,
not implemented code.

## Where the code already helps you

The engine is already split along the right seams:

- **Acquisition** (`tenderfinder_raw_sweep.py`, `tenderfinder_source_registry.py`,
  connector functions inside `tenderfinder_demo_three_buckets.py`) — pure
  fetch/normalize, no UI dependencies.
- **Scoring/routing** — heuristic keyword scoring + routing gates, isolated
  functions, easily unit-tested (see `tests\test_routing_gates.py`,
  `test_tender_signal_routing.py`).
- **Email intake** (`tenderfinder_email_intake.py`) — provider-neutral,
  credential-free, already a clean module.
- **Presentation** — currently openpyxl workbook writers; the only layer that
  must be replaced for an app.
- **Safety layer** (`tenderfinder_guards.py`, anti-fixture guard, write gates,
  run logs) — port as-is; it is the most valuable non-obvious IP here.

## Phase 1 — Refactor to a package + CLI (1–2 weeks of work)

1. Split `tenderfinder_demo_three_buckets.py` (~8k lines) into a package:
   `acquisition/`, `scoring/`, `reporting/`, `intake/`, `safety/`.
2. Introduce a `pyproject.toml`, make it `pip install`-able, expose a single
   CLI (`tenderfinder run --offline`, `tenderfinder intake …`).
3. Replace ad-hoc dict rows with typed models (dataclasses/pydantic).
4. Convert the 23 script-tests to pytest (they are already close).

## Phase 2 — Local database + scheduler (desktop app backbone)

1. Add SQLite storage for leads/tenders/sources/runs (the workbook becomes an
   *export*, not the datastore). Keep the dedupe keys (`stable_lead_id`,
   `raw_hash`) — they were designed for exactly this.
2. Background scheduler (APScheduler or Windows Task Scheduler) for daily
   sweeps + email-folder polling.
3. Desktop UI options, cheapest first:
   - keep Tkinter but read from SQLite (minimal change),
   - or **pywebview/Tauri + a local FastAPI backend** (recommended: the same
     API serves the web phase later),
   - package with PyInstaller (the macOS scripts in `packaging\` show the
     multi-platform intent).

## Phase 3 — Web platform (multi-user)

1. FastAPI backend over the same engine package; Postgres instead of SQLite.
2. Workers (Celery/RQ) run connectors; rate-limit and robots-respect per
   source — keep the "no scraping behind logins" rule from the source registry.
3. React (or similar) frontend with the three-bucket board, source health
   dashboard (Source_Run_Log data), outreach tracker, and weekly review flow
   (Task G methodology from `03 Active and QA Runbooks`).
4. Auth + per-tenant company fit profiles (the placeholder client list and
   scoring keywords in `00_Context` become per-tenant settings).
5. Email intake as an inbound mailbox (e.g. SES/Mailgun inbound → the existing
   `.eml` parser, unchanged).

## Phase 4 — Intelligence upgrades

- LLM scoring: the prompt pack in `05_PROMPTS\` was designed for exactly this;
  wire it behind a batch API with the heuristic score as fallback (the
  `tenderfinder_agent2.py` reference implementation already sketches
  batch-prompt scoring with strict JSON parsing).
- Conversion tracking: which "future" leads became real tenders (Task G
  Capture & Conversion sheet describes the metric model).
- Watchlists/alerts per user; developer relationship graph (the
  Developer_Watchlist parent-brand grouping logic is the seed).

## Guardrails to preserve at every phase

- Never store portal credentials; email/manual import only for gated sources.
- Keep the anti-fixture guard and write-gates between "collected" and
  "presented as production".
- Keep run logs + raw evidence capture (auditability is the product's trust
  story).
- Respect source terms: public pages only, no login scraping, polite rates.
