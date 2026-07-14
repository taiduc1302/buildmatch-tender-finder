from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tenderfinder_demo_three_buckets import SourceLog, infer_source_type, map_source_final_status  # noqa: E402


def main() -> int:
    base = dict(source_id="bc_bid_public", source_name="BC Bid public open opportunities", source_type=infer_source_type("bc_bid_public", "https://bcbid.gov.bc.ca"), url="https://bcbid.gov.bc.ca")
    ok = SourceLog(**base, status="OK_BROWSER_COOKIE_REPLAY", open_candidates=4)
    browser = SourceLog(**base, status="BC_BID_BLOCKED_BROWSER_CHECK_USER_ACTION_REQUIRED")
    blocked = SourceLog(**base, status="BC_BID_BLOCKED_NO_PUBLIC_FEED")

    assert map_source_final_status(ok) == "FETCH_OK_OPEN_FOUND"
    assert map_source_final_status(browser) == "BLOCKED_BROWSER_CHECK"
    assert map_source_final_status(blocked) == "BLOCKED_FORBIDDEN"

    print("BC Bid preflight mapping tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
