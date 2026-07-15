#!/usr/bin/env python3
"""Command-line entry point for the shared offline TENDER_FINDER Self-Test."""
from __future__ import annotations

import argparse
from pathlib import Path

from tenderfinder_engine import run_self_test


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the shared, strictly offline TENDER_FINDER Self-Test.")
    parser.add_argument("--root", type=Path, default=None, help="Package root (normally auto-detected).")
    parser.add_argument("--output-root", type=Path, default=None, help="Self-Test output parent.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = run_self_test(
            root=args.root,
            output_root=args.output_root,
            on_line=lambda line: print(line, flush=True),
        )
    except Exception as exc:
        print(f"SELF_TEST: FAIL - preflight/runner error: {exc}", flush=True)
        return 1
    print(f"SELF_TEST_MANIFEST: {result.manifest_path}", flush=True)
    print(f"SELF_TEST_OUTPUT: {result.out_dir}", flush=True)
    return result.return_code


if __name__ == "__main__":
    raise SystemExit(main())
