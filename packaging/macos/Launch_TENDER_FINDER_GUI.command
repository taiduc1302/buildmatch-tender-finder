#!/bin/bash
# TENDER_FINDER Tender Intelligence - GUI launcher (macOS)
# Double-click to open the TENDER_FINDER window. Run setup_tenderfinder_environment.command
# once first. If macOS refuses to open this file, right-click it and
# choose Open, or run: chmod +x *.command
set -u
cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
    echo "ERROR: TENDER_FINDER's Python environment was not found."
    echo "Run setup_tenderfinder_environment.command first (one time only)."
    read -r -p "Press Return to close..."
    exit 1
fi

# Use pythonw when the venv provides it (framework Python builds);
# otherwise plain python launches Tkinter fine on modern macOS.
PY=".venv/bin/python"
if [ -x ".venv/bin/pythonw" ]; then
    PY=".venv/bin/pythonw"
fi

exec "$PY" "01 Code/CONNECTOR_SWEEP/tenderfinder_launcher_gui.py"
