#!/usr/bin/env python3
"""Tiny unit test for search API/key/quota diagnostics.
Does not make network calls and does not print secrets.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tenderfinder_live_link_checker as c

class FakeResp:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)
    def json(self):
        return self._payload

cases = [
    (401, {"detail": "Invalid API key"}, "SEARCH_API_KEY_INVALID_OR_FORBIDDEN"),
    (403, {"detail": "Forbidden"}, "SEARCH_API_KEY_INVALID_OR_FORBIDDEN"),
    (429, {"detail": "Usage limit reached"}, "SEARCH_API_QUOTA_OR_RATE_LIMIT"),
    (402, {"detail": "Payment required"}, "SEARCH_API_PAYMENT_OR_PLAN_REQUIRED"),
    (500, {"detail": "Provider failure"}, "SEARCH_API_PROVIDER_5XX"),
]

for status, payload, expected in cases:
    try:
        c._raise_for_search_response("tavily", FakeResp(status, payload))
        raise AssertionError(f"Expected exception for HTTP {status}")
    except c.SearchProviderError as exc:
        assert exc.reason == expected, (status, exc.reason, expected)

# Local env/key loader should not expose the key, just confirm presence/absence as a boolean.
assert isinstance(c.has_search_api_key("tavily"), bool)
print("search_api_error_mapping: PASS")
