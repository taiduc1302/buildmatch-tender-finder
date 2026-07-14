# Patch 5.17 Backlog

## BC Bid Public Browse - Note on This Run's Status

- This file was auto-generated from the demo_p516 committed build, which happened to hit BC Bid's browser-check wall (see the raw status below). Read that in context, not as a persistent regression: the cookie-replay + closing-date-aware pagination connector was live-verified working repeatedly during Patch 5.16 development (~203-204 candidates parsed across 15 pages, hard_cap_reached as the stop reason, 46 civil_relevant=YES after the keyword fixes). The block on this specific commit's build run is most likely BC Bid's own bot-detection responding to the volume of automated Playwright sessions this sandbox made against bcbid.gov.bc.ca while developing and testing Patches 5.13-5.16 today, not a code defect. A future patch/run against BC Bid should expect this connector to work again once request volume from this environment settles down; if it doesn't, re-run the direct diagnostic (`sweep_bc_bid_public`) in isolation first, exactly as Patch 5.15's Track 0 did for the municipal-source regression, before assuming the pagination/keyword logic itself is broken.

## BC Bid Public Browse Still Blocked (this run)

- Status: `BC_BID_BLOCKED_NO_PUBLIC_FEED`
- Evidence: Playwright audit landed on `https://bcbid.gov.bc.ca/page.aspx/en/bas/browser_check` with title `Browser check: BC Bid` and a reCAPTCHA-backed browser-check flow before any opportunities API was exposed.
- Reference: `docs/BC_BID_NETWORK_AUDIT.md`
- Next real unlock: either BC Bid exposes a documented public opportunities feed/API, or the business chooses a manual/browser-reviewed workflow outside TENDER_FINDER automation.
