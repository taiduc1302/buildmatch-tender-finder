#!/usr/bin/env python3
"""Offline compatibility check for the minimum supported OpenAI Python SDK."""
from __future__ import annotations

import inspect

from openai import OpenAI


def main() -> int:
    client = OpenAI(api_key="sk-ci-placeholder")
    try:
        responses = getattr(client, "responses", None)
        if responses is None:
            raise RuntimeError("OpenAI client has no 'responses' resource")

        create = getattr(responses, "create", None)
        if not callable(create):
            raise RuntimeError("OpenAI client.responses.create is not callable")

        params = inspect.signature(create).parameters
        required = {"model", "input", "text", "timeout"}
        missing = sorted(required.difference(params))
        if missing:
            raise RuntimeError(
                "responses.create is missing arguments used by "
                f"tenderfinder_ai_analysis.py: {', '.join(missing)}"
            )
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()

    print("OPENAI_MINIMUM_COMPAT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
