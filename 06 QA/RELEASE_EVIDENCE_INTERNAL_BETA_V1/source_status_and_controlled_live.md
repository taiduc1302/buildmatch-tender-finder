# Source status and controlled live evidence

## Canonical registry status

After the controlled Surrey proof, `config/sources.csv` reports:

| Category | Count |
| --- | ---: |
| Total configured | 39 |
| Enabled | 39 |
| Runtime eligible | 27 |
| Verified live | 1 |
| Ready for live testing | 26 |
| Adapter fixture passed | 0 |
| Config valid only | 0 |
| Needs configuration | 3 |
| Manual only | 4 |
| Blocked | 1 |
| Wrong source | 4 |
| Deprecated | 0 |

These categories are not merged. `enabled` remains founder-controlled and does
not mean that a source was parser-tested, live-verified, or operational.

## Controlled public BC live proof

The bounded preview tested exactly two explicit public development sources,
five rows each, with no credentials, broad crawl, retry loop, login, or access
control bypass:

- `surrey_devapps_v2`: HTTP 200; parser used; 5 raw, 5 normalized, 0 rejected;
  four records scored HIGH/MEDIUM and routed as relevant. Result:
  `PASS_LIVE_SOURCE`.
- `abbotsford_devapps`: HTTP 200; parser used; 5 raw, 5 normalized, 0 rejected;
  all five records were thin/LOW. Result: `LIVE_SOURCE_REVIEW_REQUIRED`; it was
  not promoted.

Preview evidence:
`C:\tenderfinder_out\release_evidence_work\controlled_live\filtered_preview\controlled_live_proof.json`.

A separate Surrey-only run persisted the successful metadata atomically and
created an external registry backup. Surrey became the sole `verified_live`
source. The final request URL is retained as audit evidence while the reusable
base layer remains `last_good_endpoint`.

Persisted evidence:
`C:\tenderfinder_out\release_evidence_work\controlled_live\final_surrey_v2\controlled_live_proof.json`.

The proof JSON records `manual_sample_review: PENDING_AGENT_REVIEW` because the
script emitted the file before this review. Codex subsequently inspected the
five sanitized samples: four contained meaningful current project details and
HIGH/MEDIUM scores; the fifth was a clearly identified LOW sidewalk record.
That manual review supports Surrey's PASS and does not alter the immutable raw
proof file.

The other 37 configured sources were not live-tested and no claim is made that
they work.
