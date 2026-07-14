# Tavily key setup and error handling

This Patch 4.1 package is configured to use Tavily as the default replacement-search provider.

The checker reads the key from either:

1. the environment variable `TAVILY_API_KEY`, or
2. a local file in this folder named `.env.tenderfinder.local`.

The local `.env.tenderfinder.local` file is intentionally private. Do not share this package outside your own machine while that file contains a real key.

## Run without replacement search

```bash
python tenderfinder_raw_sweep.py \
  --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx" \
  --preflight-links \
  --preflight-no-search \
  --preflight-output-dir "./link_audit_out"
```

## Run with Tavily replacement search

```bash
python tenderfinder_raw_sweep.py \
  --from-master "../../00 Master/TENDER_FINDER_Tender_Intelligence_Working_Master_v6.xlsx" \
  --preflight-links \
  --preflight-search-provider tavily \
  --preflight-output-dir "./link_audit_out"
```

## Key/quota diagnostics

If Tavily fails because the key is missing, invalid, forbidden, exhausted, or rate-limited, the checker now records an explicit replacement reason such as:

- `SEARCH_SKIPPED_NO_API_KEY`
- `SEARCH_API_KEY_INVALID_OR_FORBIDDEN`
- `SEARCH_API_QUOTA_OR_RATE_LIMIT`
- `SEARCH_API_PAYMENT_OR_PLAN_REQUIRED`
- `SEARCH_API_TIMEOUT`
- `SEARCH_API_CONNECTION_ERROR`

These are search API/key/quota problems. They are not proof that the original source URL is valid or invalid.
