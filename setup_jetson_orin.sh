#!/bin/bash

# Automatic setup script for Jetson AGX Orin
# Uses pyproject-jetson-orin.toml as the active Poetry configuration.
#
# HOW TO RUN from the project root:
#   bash setup_jetson_orin.sh
#
# This script:
# 1. Activates pyproject-jetson-orin.toml by copying it to pyproject.toml.
# 2. Rebuilds poetry.lock for the Jetson Orin environment.
# 3. Installs project dependencies with Poetry.
# 4. Checks installed torch and accelerate versions.
# 5. Reinstalls torch/accelerate only when needed.
# 6. Verifies CUDA availability.
#
# Requirements:
# - Poetry installed.
# - Python compatible with the project.
# - CUDA configured on Jetson AGX Orin.
# - Access to the Jetson AI Lab package index.

set -e

TORCH_VERSION="2.8.0"
ACCELERATE_VERSION="1.2.1"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JETSON_TOML="$PROJECT_ROOT/pyproject-jetson-orin.toml"
PYPROJECT_TOML="$PROJECT_ROOT/pyproject.toml"
POETRY_LOCK="$PROJECT_ROOT/poetry.lock"

echo ""
echo "=============================================="
echo "Jetson AGX Orin Setup"
echo "=============================================="
echo "Project directory: $PROJECT_ROOT"
echo ""

cd "$PROJECT_ROOT"

# Step 0: Check prerequisites.
echo "0 - Checking prerequisites..."
echo ""

if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "  OK Python: $PYTHON_VERSION"
else
    echo "  ERROR Python3 not found. Install a compatible version."
    exit 1
fi

if command -v poetry >/dev/null 2>&1; then
    POETRY_VERSION=$(poetry --version 2>&1)
    echo "  OK Poetry: $POETRY_VERSION"
else
    echo "  ERROR Poetry not found. Install Poetry before continuing."
    exit 1
fi

if command -v nvidia-smi >/dev/null 2>&1; then
    echo "  OK NVIDIA driver: available"
else
    echo "  WARNING nvidia-smi not found. This may be normal on some Jetson setups."
fi

# Step 1: Activate Jetson Orin configuration.
echo ""
echo "1 - Copying Jetson Orin configuration..."

if [ ! -f "$JETSON_TOML" ]; then
    echo "  ERROR pyproject-jetson-orin.toml not found at:"
    echo "  $JETSON_TOML"
    exit 1
fi

cp "$JETSON_TOML" "$PYPROJECT_TOML"
echo "  OK Copied pyproject-jetson-orin.toml to pyproject.toml"
echo "  INFO Original file preserved"

# Step 2: Rebuild lock file.
echo ""
echo "2 - Rebuilding poetry.lock for Jetson Orin..."

if [ -f "$POETRY_LOCK" ]; then
    rm -f "$POETRY_LOCK"
    echo "  OK Removed previous poetry.lock"
fi

echo "  Running poetry lock..."
poetry lock
echo "  OK poetry.lock created"

# Step 3: Install Poetry dependencies.
echo ""
echo "3 - Installing project dependencies..."
echo "  Running poetry install..."
poetry install
echo "  OK Dependencies installed"

# Helper function to check package version inside the Poetry environment.
check_package_version() {
    local package_name="$1"

    poetry run python3 - <<PY 2>/dev/null || echo "NOT_INSTALLED"
try:
    import ${package_name}
    print(${package_name}.__version__)
except Exception:
    print("NOT_INSTALLED")
PY
}

# Step 4: Check installed versions.
echo ""
echo "4 - Checking installed versions..."

TORCH_INSTALLED=$(check_package_version "torch")
ACCELERATE_INSTALLED=$(check_package_version "accelerate")

echo "  - torch:      $TORCH_INSTALLED (required: $TORCH_VERSION)"
echo "  - accelerate: $ACCELERATE_INSTALLED (required: $ACCELERATE_VERSION)"

NEED_TORCH=false
NEED_ACCELERATE=false

if [ "$TORCH_INSTALLED" != "$TORCH_VERSION" ]; then
    NEED_TORCH=true
fi

if [ "$ACCELERATE_INSTALLED" != "$ACCELERATE_VERSION" ]; then
    NEED_ACCELERATE=true
fi

# Step 5: Install/update accelerate when needed.
echo ""
if [ "$NEED_ACCELERATE" = true ]; then
    echo "5 - Installing accelerate $ACCELERATE_VERSION..."
    poetry run pip install --no-deps "accelerate==$ACCELERATE_VERSION"
    echo "  OK accelerate updated"
else
    echo "5 - accelerate is already at the required version"
fi

# Step 6: Install/update torch when needed.
echo ""
if [ "$NEED_TORCH" = true ]; then
    echo "6 - Installing torch $TORCH_VERSION from Jetson AI Lab..."
    poetry run pip install --force-reinstall --no-cache-dir "torch==$TORCH_VERSION" \
        --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
    echo "  OK torch updated"
else
    echo "6 - torch is already at the required version"
fi

# Step 7: Verify final installation.
echo ""
echo "7 - Verifying installation..."

poetry run python3 <<'VERIFY'
import sys
import torch
import accelerate

print(f"OK torch:        {torch.__version__}")
print(f"OK accelerate:   {accelerate.__version__}")
print(f"OK CUDA:         {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"OK device:       {torch.cuda.get_device_name(0)}")
else:
    print("ERROR CUDA is not available.")
    sys.exit(1)
VERIFY

echo ""
echo "=============================================="
echo "OK Setup completed successfully!"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "  To run the REST API:"
echo "    poetry run ar-api"
echo ""
echo "  To run the manual pipeline test:"
echo "    poetry run python tests/manual/test_pipeline.py"
echo ""
echo "  To run unit tests:"
echo "    poetry run pytest tests/"
echo ""
echo "=============================================="