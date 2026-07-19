# Live OpenAI Analysis Results (Phase 3)

## Key detection

`OPENAI_API_KEY` present: **NO** (confirmed via `os.environ` inspection and a
full environment scan; no `.env` file, no credential file of any kind found
anywhere reachable from this session).
`openai` SDK: installed and verified importable (`openai==2.46.0`) —
previously undeclared in `requirements.txt`; now added to both
`requirements.txt` and `01 Code/CONNECTOR_SWEEP/requirements.txt`.

## What was verified without a live call

* `tenderfinder_ai_analysis._default_client_factory()` correctly constructs a
  real `openai.OpenAI` client object with `responses.create` available, given
  a syntactically valid key — confirmed by direct construction test (dummy
  key, no network call made).
* `analyze_opportunity(...)` with no `client_factory` and no key returns
  `STATUS_SETUP_REQUIRED` with `analysis=None` (no fabricated response) and
  setup instructions naming `OPENAI_API_KEY` — exactly the required
  missing-key behaviour.

## Full mocked test suite (SDK boundary faked; no real network/key needed)

`tests/test_buildweek_ai_analysis.py` — **23 passed, 1 skipped** (the
opt-in live smoke test). Covers: valid structured response, strict schema
supplied to the API, extra-field rejection, missing-required-field rejection,
refusal, incomplete response, invalid JSON, rate limit (bounded retry then
fail), timeout (retryable), authentication failure (not retried), retry-limit
bound, cache hit (no second call), cache invalidation on input change,
missing-key setup-required with no fabrication, prompt-injection content
handled as data (not obeyed), private-field exclusion, API key never present
in the cache key, deterministic-score preservation + disagreement flagging,
cancellation, controller rendering (deterministic vs AI sections kept
separate), controller setup-required view, JSON/Markdown export.

## Live call: genuine, documented external blocker

Per the task's own rule ("do not falsely mark the check passed... document
exact evidence"): a real live OpenAI call was **not executed** in this session
because no `OPENAI_API_KEY` exists anywhere in this environment. This is not
an outage — it is the absence of a credential this session has no way to
obtain. All code paths that *would* execute a real call (client construction,
request shape, strict-schema parameter, retry policy, caching, disagreement
detection) are implemented and covered by the mocked suite above, which
exercises the exact same code paths with a fake transport swapped in at the
one integration seam (`client_factory`).

**This blocker cannot be resolved by this session.** It requires the founder
to set `OPENAI_API_KEY` (and optionally `OPENAI_MODEL`) in an environment
where the live smoke test can then be run:

```bash
export OPENAI_API_KEY=sk-...
export TENDER_FINDER_RUN_LIVE_OPENAI=1
python3 -m pytest "01 Code/CONNECTOR_SWEEP/tests/test_buildweek_ai_analysis.py::test_live_openai_smoke" -v
```

## Model configurability

The runtime model is read from `OPENAI_MODEL` (default `gpt-5.6`, per the
competition configuration) — never hard-coded, never silently substituted. No
claim is made that any specific model is actually available; that can only be
confirmed by a real successful call, which requires the founder's own key.
