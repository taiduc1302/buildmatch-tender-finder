#!/bin/bash
# ============================================================
# TENDER_FINDER Tender Intelligence - One-Time Environment Setup (macOS)
# Patch 5.19
#
# Run this ONCE. It creates a local Python virtual environment,
# installs the packages TENDER_FINDER needs, and downloads the Playwright
# Chromium browser used by the BC Bid connector. After it
# finishes, use Launch_TENDER_FINDER_GUI.command to run TENDER_FINDER.
#
# If macOS refuses to open this file ("unidentified developer"),
# right-click it and choose Open, or run in Terminal:
#   chmod +x *.command
# ============================================================
set -u
cd "$(dirname "$0")"

echo "============================================================"
echo "TENDER_FINDER Tender Intelligence - Environment Setup (macOS)"
echo "============================================================"
echo ""

# --- Step 1: find Python 3 ----------------------------------
echo "[1/4] Checking for Python 3..."
if ! command -v python3 >/dev/null 2>&1; then
    echo ""
    echo "ERROR: python3 was not found on this Mac."
    echo ""
    echo "TENDER_FINDER needs Python 3.10 or newer. Install it either from:"
    echo "  https://www.python.org/downloads/  (recommended - includes Tk)"
    echo "or via Homebrew:"
    echo "  brew install python-tk"
    echo ""
    echo "After installing Python, run this setup script again."
    echo "============================================================"
    read -r -p "Press Return to close..."
    exit 1
fi
echo "  Found: $(python3 --version)"
echo ""

# --- Step 2: create/reuse virtual environment ----------------
echo "[2/4] Setting up the local virtual environment..."
if [ -x ".venv/bin/python" ]; then
    echo "  Existing environment found at .venv - reusing it."
else
    if ! python3 -m venv .venv; then
        echo ""
        echo "ERROR: Failed to create the virtual environment."
        echo "See the message above for details."
        read -r -p "Press Return to close..."
        exit 1
    fi
    echo "  Created .venv"
fi
VENV_PY=".venv/bin/python"
echo ""

# --- Step 3: install Python packages -------------------------
echo "[3/4] Installing required Python packages..."
REQUIREMENTS="01 Code/CONNECTOR_SWEEP/requirements.txt"
if [ ! -f "$REQUIREMENTS" ]; then
    echo ""
    echo "ERROR: Could not find requirements.txt at:"
    echo "  $REQUIREMENTS"
    read -r -p "Press Return to close..."
    exit 1
fi
"$VENV_PY" -m pip install --upgrade pip >/dev/null
if ! "$VENV_PY" -m pip install -r "$REQUIREMENTS"; then
    echo ""
    echo "ERROR: pip install failed. See the message above for details."
    read -r -p "Press Return to close..."
    exit 1
fi
echo "  Packages installed."
echo ""

# --- Step 4: install Playwright's Chromium browser ------------
echo "[4/4] Installing the Playwright Chromium browser..."
echo "  This downloads roughly 300MB and can take a few minutes the"
echo "  first time. Future setup runs skip it if already installed."
if ! "$VENV_PY" -m playwright install chromium; then
    echo ""
    echo "WARNING: Playwright browser install did not finish cleanly."
    echo "  The BC Bid connector needs this browser; other TENDER_FINDER features"
    echo "  still work. You can retry later with:"
    echo "  $VENV_PY -m playwright install chromium"
    echo ""
fi
echo ""

# Make sure all launchers in this folder are executable.
chmod +x ./*.command 2>/dev/null || true

echo "============================================================"
echo "Setup complete."
echo ""
echo "To run TENDER_FINDER, double-click:  Launch_TENDER_FINDER_GUI.command"
echo "(or run it from Terminal in this folder)"
echo "============================================================"
read -r -p "Press Return to close..."
exit 0
