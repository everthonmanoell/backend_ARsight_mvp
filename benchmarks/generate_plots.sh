#!/bin/bash
# Quick script to generate all benchmark plots.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLOTS_SCRIPTS_DIR="$SCRIPT_DIR/plots_scripts"
PLOTS_OUTPUT="$SCRIPT_DIR/plots_output"
GENERATE_ALL="$PLOTS_SCRIPTS_DIR/generate_all.py"

echo "============================================================"
echo "Generating benchmark plots"
echo "============================================================"

if [ ! -f "$GENERATE_ALL" ]; then
    echo "ERROR generate_all.py not found at:"
    echo "  $GENERATE_ALL"
    exit 1
fi

cd "$PLOTS_SCRIPTS_DIR"

echo ""
echo "Scripts directory: $PLOTS_SCRIPTS_DIR"
echo ""

# Check whether Poetry is available.
if command -v poetry >/dev/null 2>&1; then
    echo "Poetry found. Running with poetry run..."
    poetry run python generate_all.py
else
    echo "Poetry not found. Running with system python..."
    python generate_all.py
fi

echo ""
echo "============================================================"
echo "Benchmark plots generated successfully"
echo "============================================================"

echo ""
echo "Files saved to: $PLOTS_OUTPUT"
echo ""

echo "Generated PNG files:"
ls -lh "$PLOTS_OUTPUT"/*.png 2>/dev/null || echo "  No PNG files found yet."
echo ""

if [ -f "$PLOTS_OUTPUT/index.html" ]; then
    echo "HTML report:"
    echo "  $PLOTS_OUTPUT/index.html"
    echo ""
    echo "To open it in a browser:"
    echo "  xdg-open $PLOTS_OUTPUT/index.html"
fi

echo ""
echo "Done."