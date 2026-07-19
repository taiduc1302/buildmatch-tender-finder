# Three-Minute Demo (Final)

See `docs/buildweek/07_THREE_MINUTE_DEMO.md` for the full script — it was
updated in this session to reflect the real 82-record Public Snapshot and the
new Ranked Opportunities selection UI (the AI action now requires an actual
selected row, not an auto-picked top-ranked record).

Summary of what changed since the previous draft of this demo:

1. **Real data, not fictitious** — the snapshot now contains 82 real, sanitized
   public development-application records from 5 BC municipalities, captured
   via the same production sweep the "Refresh Development Data" button uses.
2. **Genuine selection, not auto-pick** — step 6 of the demo now shows clicking
   a specific row in the Ranked Opportunities table before running AI analysis,
   demonstrating that the tool never substitutes a different opportunity for
   the one the estimator chose.
3. **Optional live-refresh beat** — the demo script now explicitly calls out a
   brief, optional live-refresh demonstration against the same real public
   sources proven in `03_CONTROLLED_LIVE_REFRESH_RESULTS.md`, with honest
   source-health reporting (Vancouver rezoning/permit sources correctly shown
   as `needs_configuration`, never selected).

Fallback behaviour (public source down / OpenAI unavailable) is unchanged and
documented in `docs/buildweek/07_THREE_MINUTE_DEMO.md`.
