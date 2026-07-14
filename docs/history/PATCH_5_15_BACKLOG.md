# Patch 5.15 Backlog

## BC Bid Connector - Remaining Volume Gap

- Status: `OK_BROWSER_COOKIE_REPLAY` with pagination (Patch 5.14)
- Current capability: cookie-replay connector now clicks through the AJAX grid pager (`#body_x_grid_gridPagerBtnNextPage`) and parses up to 5 pages per run; this run fetched 5 page(s) and the grid reports `More than 150 Record(s)`.
- Gap still open: the page cap (5) is well below the full listing ("More than 150 Record(s)"), so a future patch should raise the cap or switch to a smarter stop condition (e.g. stop once closing dates roll past a relevance window) instead of a flat page count.
- Detail-page contact recovery: attempted 17 civil+open rows this run, recovered contact info for 9 that had none before. Rows without a published contact email/phone on the detail page (BC Bid routes most enquiries through its internal messaging system) remain blank by design, not a parsing failure.
- Reference: `docs/BC_BID_NETWORK_AUDIT.md`
