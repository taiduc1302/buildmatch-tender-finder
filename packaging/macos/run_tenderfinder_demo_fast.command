#!/bin/bash
# ============================================================
# TENDER_FINDER Fast Demo Launcher (macOS)
# Uses --no-fetch for bad wifi. Track A, Action Center, and the
# intake plan still build without touching live tender sites.
# Uses the SAME review workbook default as run_tenderfinder_demo.command
# and the GUI - fast and full mode must never silently disagree
# on Track A because of a stale hardcoded path (Patch 5.18).
# ============================================================
set -u
cd "$(dirname "$0")"

# Review workbook lookup order: env var, package-local inputs/, legacy path.
REVIEW_XLSX="$HOME/tenderfinder_out/patch5_10_live/all_live_review.xlsx"
if [ -f "inputs/all_live_review.xlsx" ]; then
    REVIEW_XLSX="inputs/all_live_review.xlsx"
fi
if [ -n "${TENDER_FINDER_REVIEW_XLSX:-}" ]; then
    REVIEW_XLSX="$TENDER_FINDER_REVIEW_XLSX"
fi
OUT_DIR="$HOME/tenderfinder_out/demo_mac_fast"

SCRIPT="01 Code/CONNECTOR_SWEEP/tenderfinder_demo_three_buckets.py"
WORKBOOK="$OUT_DIR/TENDER_FINDER_DEMO_Opportunities_Three_Buckets.xlsx"
SUMMARY="$OUT_DIR/demo_summary.txt"

PY=".venv/bin/python"
if [ ! -x "$PY" ]; then
    echo "ERROR: TENDER_FINDER's Python environment was not found."
    echo "Run setup_tenderfinder_environment.command first (one time only)."
    read -r -p "Press Return to close..."
    exit 1
fi

if [ ! -f "$SCRIPT" ]; then
    echo "ERROR: Demo builder not found: $SCRIPT"
    read -r -p "Press Return to close..."
    exit 1
fi

if [ ! -f "$REVIEW_XLSX" ]; then
    echo "ERROR: Review workbook not found: $REVIEW_XLSX"
    echo "Copy it to that path, or edit REVIEW_XLSX at the top of this"
    echo "launcher, or set the TENDER_FINDER_REVIEW_XLSX environment variable."
    read -r -p "Press Return to close..."
    exit 1
fi

if ! "$PY" "$SCRIPT" --review-xlsx "$REVIEW_XLSX" --out-dir "$OUT_DIR" --email-intake --no-fetch; then
    echo "ERROR: TENDER_FINDER fast demo build failed."
    read -r -p "Press Return to close..."
    exit 1
fi

[ -d "$OUT_DIR" ] && open "$OUT_DIR"
[ -f "$WORKBOOK" ] && open "$WORKBOOK"

if [ -f "$SUMMARY" ]; then
    cat "$SUMMARY"
else
    echo "============================================================"
    echo "TENDER_FINDER FAST DEMO COMPLETE - summary file missing."
    echo "Workbook: $WORKBOOK"
    echo "============================================================"
fi

read -r -p "Press Return to close..."
exit 0
