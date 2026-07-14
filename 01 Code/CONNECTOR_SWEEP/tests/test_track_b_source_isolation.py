from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tenderfinder_demo_three_buckets import TENDER_SOURCES, sweep_source  # noqa: E402

# Patch 5.15 regression guard. Patch 5.14 ran BC Bid's heavy Playwright
# sweep (~20-25s, real headless browser) inside the same ThreadPoolExecutor
# batch as every lightweight municipal HTTP source. That caused
# intermittent zero-candidate results from otherwise-working sources
# (surrey_bids_public, richmond_procurement) in the same run, confirmed by
# repeated repro with identical code: those sources flipped between their
# normal counts and 0 across runs, with no abnormal elapsed time on the
# failing runs. The fix in Patch 5.15 runs BC Bid's sweep on its own, never
# overlapping with the other sources. This test makes a real network call
# (consistent with the rest of the live regression suite) to prove
# surrey_bids_public still returns its normal candidate range when it runs
# in the same process right after a BC Bid fetch.


def main() -> int:
    bc_bid_source = next(s for s in TENDER_SOURCES if s["source_id"] == "bc_bid_public")
    surrey_source = next(s for s in TENDER_SOURCES if s["source_id"] == "surrey_bids_public")

    bc_result = sweep_source(bc_bid_source)
    print(f"bc_bid_public: status={bc_result.log.status} candidates={bc_result.log.candidates}")

    surrey_result = sweep_source(surrey_source)
    print(f"surrey_bids_public: status={surrey_result.log.status} candidates={surrey_result.log.candidates}")

    assert surrey_result.log.candidates > 0, (
        f"surrey_bids_public returned 0 candidates right after a BC Bid sweep in the same process "
        f"(status={surrey_result.log.status}, note={surrey_result.log.note!r}); "
        "this is the Patch 5.14 starvation regression"
    )
    assert surrey_result.log.status == "OK_HTML", surrey_result.log.status

    print("Track B source isolation test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
