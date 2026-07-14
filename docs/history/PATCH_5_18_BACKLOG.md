# Patch 5.18 Backlog

## BC Bid Connector - Remaining Volume Gap

- Status: `OK_BROWSER_COOKIE_REPLAY` with closing-date-aware pagination (Patch 5.16)
- Current capability: cookie-replay connector clicks through the AJAX grid pager (`#body_x_grid_gridPagerBtnNextPage`) while each fetched page still has at least one row closing within 90 days, up to a hard bound of 15 pages; this run fetched 15 page(s), stopped because `hard_cap_reached (15 pages)`, and the grid reports `More than 150 Record(s)`.
- Gap still open: live-verified during Patch 5.16 that BC Bid's grid still had an enabled Next button after 15 pages (~220+ rows), all still within the 90-day relevance window, meaning the hard cap - not the relevance window - is the practical stop today. A future patch could raise the hard cap further or make it adaptive (e.g. based on total elapsed time budget) if more volume is needed, but only after re-confirming this doesn't reintroduce the Patch 5.14 municipal-source starvation Patch 5.15 fixed (tests/test_track_b_source_isolation.py must keep passing).
- Detail-page contact recovery: attempted 49 civil+open rows this run, recovered contact info for 29 that had none before. Rows without a published contact email/phone on the detail page (BC Bid routes most enquiries through its internal messaging system) remain blank by design, not a parsing failure.
- Reference: `docs/BC_BID_NETWORK_AUDIT.md`
