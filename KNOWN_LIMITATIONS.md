# Known Limitations

- This is an internal weekly Windows/Python beta, not production-ready and not
  a self-contained executable. First launch installs dependencies.
- Many of the 39 configured source rows are not currently live-verified.
  Configured, enabled, fixture-tested, and verified-live counts are separate.
- Public pages can change structure, block automation, or expose zero current
  opportunities. A test proves only the source and timestamp recorded.
- BC Bid may present a browser check/CAPTCHA. Tender Finder does not bypass or
  solve it and reports that source as unavailable for the run.
- Manual Email Alert Intake reads approved local `.eml` files. Gmail/Outlook
  OAuth and IMAP are not implemented; source messages are never moved/deleted.
- An adapter-level fixture proves shared parser behavior, not every source that
  uses that adapter. Missing source-specific fixtures are not mislabeled PASS.
- A disabled `custom` source draft cannot run until a compatible code adapter
  is implemented.
- A historical Vancouver permit without sufficient persisted raw scoring text
  retains its source-specific legacy permit tier, visibly audited. New and
  replayable records with snapshots are recomputed.
- Never-persisted tender candidates cannot be retroactively rescored; newly
  parsed candidates always use the current effective keywords.
- `01 Code/tenderfinder_agent2.py` is frozen legacy code and remains outside the
  GUI/engine pipeline.
- BuildMatch/Neon synchronization, multi-user state, scheduling, and a hosted
  web UI are not implemented. The JSON engine boundary is future-facing only.
