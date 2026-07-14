# Patch 5.16 Backlog

## BC Bid Connector - Remaining Volume Gap

- Status: `OK_BROWSER_COOKIE_REPLAY` with pagination (Patch 5.14)
- Current capability: cookie-replay connector now clicks through the AJAX grid pager (`#body_x_grid_gridPagerBtnNextPage`) and parses up to 5 pages per run; this run fetched 5 page(s) and the grid reports `More than 150 Record(s)`.
- Gap still open: the page cap (5) is well below the full listing ("More than 150 Record(s)"), so a future patch should raise the cap or switch to a smarter stop condition (e.g. stop once closing dates roll past a relevance window) instead of a flat page count.
- Detail-page contact recovery: attempted 13 civil+open rows this run, recovered contact info for 6 that had none before. Rows without a published contact email/phone on the detail page (BC Bid routes most enquiries through its internal messaging system) remain blank by design, not a parsing failure.
- Patch 5.15 also resequenced Track B so BC Bid's heavy Playwright sweep never overlaps with the lightweight municipal HTTP sources in the same run (it previously starved sources like surrey_bids_public intermittently when run inside the same thread pool batch). A future patch could explore running BC Bid concurrently again with a dedicated resource budget if total demo build time needs to shrink, but only with the regression guard in tests/test_track_b_source_isolation.py proving it stays safe.
- Reference: `docs/BC_BID_NETWORK_AUDIT.md`
