# Tavily Key Integration Changelog

## Purpose

Add a safe Tavily replacement-search configuration to the accepted Patch 4 HOTFIX baseline.

## Files added

- `.env.tenderfinder.local` — local private Tavily key file for this package copy.
- `.env.tenderfinder.local.example` — template for replacing/rotating the key.
- `.gitignore` — ignores local secret files and generated audit output when using git.
- `TAVILY_KEY_SETUP_AND_ERRORS.md` — operator guide for Tavily setup and error meanings.
- `tests/test_search_api_errors.py` — no-network unit test for search API/key/quota diagnostic mapping.

## Files modified

- `tenderfinder_live_link_checker.py`
  - loads optional local env files without python-dotenv;
  - defaults replacement search provider to Tavily;
  - raises explicit `SearchProviderError` diagnostics instead of hiding provider failures as empty results;
  - records explicit replacement reasons such as `SEARCH_API_QUOTA_OR_RATE_LIMIT` and `SEARCH_API_KEY_INVALID_OR_FORBIDDEN`.

- `tenderfinder_link_preflight.py`
  - default integrated preflight search provider changed to Tavily.

- `tenderfinder_raw_sweep.py`
  - default `--preflight-search-provider` changed to Tavily.

## Guardrails

- The key is not hardcoded into Python code.
- If the key is missing, invalid, forbidden, exhausted, or rate-limited, the checker should say so through `replacement_reason` and logs.
- A Tavily/key/quota error is not treated as proof that the original source URL is valid or invalid.
- Running with `--preflight-no-search` still works and does not require any API key.

## Verification performed in this environment

- `python -m py_compile tenderfinder_raw_sweep.py tenderfinder_link_preflight.py tenderfinder_live_link_checker.py` — PASS
- `python tenderfinder_raw_sweep.py --help` — PASS
- `python tenderfinder_live_link_checker.py --help` — PASS
- imported checker and confirmed Tavily key is loaded as a boolean without printing it — PASS
- integrated dry-run through `tenderfinder_raw_sweep.py` — PASS, 68 source rows / 68 URLs / all 7 outputs created
- `python tests/test_search_api_errors.py` — PASS

## Not verified here

A real live Tavily API call was not executed in this sandbox. Run on a normal machine/network to confirm live replacement search behavior.
