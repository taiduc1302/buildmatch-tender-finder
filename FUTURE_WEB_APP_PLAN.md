# Future Web / BuildMatch Boundary

Today Tender Finder is a clickable Tkinter desktop beta with Excel outputs and
a GUI-independent JSON engine. BuildMatch/Neon synchronization, a hosted UI,
database-backed multi-user state, and scheduling are not implemented.

## Existing seam

`tenderfinder_engine.py` imports no Tkinter and exposes serializable
`RunRequest`, run plan, `EngineRunResult`, source validation/test results,
manifests, warnings, errors, source/record/bucket counts, and output paths. The
desktop GUI calls that layer rather than duplicating core orchestration.

Supporting seams are:

- acquisition/normalization: source registry, adapters, raw sweep, email intake;
- scoring/routing: current `keywords.xlsx`, guards, unified replay scorer;
- output/preservation: workbook writer, stable IDs, manual-field carry-forward;
- safety/audit: public URL policy, formula-injection guard, manifests, Self-Test.

## Feasible future integration

A future service could invoke the engine and map normalized records into
BuildMatch using its importer contract (for example `sourceName + externalId`).
The two products currently have separate keyword stores: Tender Finder's Excel
file and BuildMatch's database table. Sharing one source of truth is feasible
through a future sync/API adapter, but conflict ownership, versioning, audit,
offline behavior, and tenant boundaries must be decided before implementation.

## Guardrails for future work

- Keep source fetching behind explicit public/no-login policies and rate limits.
- Preserve formula/URL safety and source-test truthfulness.
- Keep user manual fields and rule-change audit history.
- Do not couple a web API to Tkinter or parse GUI text.
- Treat Excel as an editable/export interface unless a deliberately migrated
  database becomes authoritative.

This document notes feasibility only; it does not claim the integration exists.
