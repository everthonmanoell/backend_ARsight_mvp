#!/bin/bash

# Poetry setup script for Jetson Nano without Docker.
# Installs and runs the project directly on Jetson Nano using Poetry.
#
# HOW TO RUN from the project root:
#   bash setup_poetry_nano.sh
#
# After setup:
#   poetry run python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000
#
# Target environment:
# - Jetson Nano
# - L4T R32.7.x / JetPack 4.6.x
# - CUDA 10.2
# - Python 3.6

set -e

# Jetson Nano fix: force OpenBLAS to use ARMv8 kernels.
# Without this, numpy/cv2/torch may fail with "Illegal instruction" on ARM.
export OPENBLAS_CORETYPE=ARMV8

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NANO_TOML="$PROJECT_ROOT/pyproject-jetson-nano.toml"
PYPROJECT_TOML="$PROJECT_ROOT/pyproject.toml"
POETRY_LOCK="$PROJECT_ROOT/poetry.lock"

echo ""
echo "=============================================="
echo "Jetson Nano Poetry Setup"
echo "L4T R32.7.x / JetPack 4.6.x"
echo "=============================================="
echo "Project directory: $PROJECT_ROOT"
echo ""

cd "$PROJECT_ROOT"

# Step 0: Check Python.
echo "0 - Checking Python..."
PYTHON_VERSION=$(python3 --version 2>&1)
echo "  OK Python: $PYTHON_VERSION"

# Step 1: Check or install Poetry.
if ! command -v poetry >/dev/null 2>&1; then
    echo ""
    echo "1 - Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    echo "  OK Poetry installed"
else
    echo ""
    echo "1 - Poetry already installed"
    poetry --version
fi

# Step 2: Activate Jetson Nano pyproject.
echo ""
echo "2 - Configuring pyproject.toml..."

if [ ! -f "$NANO_TOML" ]; then
    echo "  ERROR pyproject-jetson-nano.toml not found at:"
    echo "  $NANO_TOML"
    exit 1
fi

cp "$NANO_TOML" "$PYPROJECT_TOML"
echo "  OK Copied pyproject-jetson-nano.toml to pyproject.toml"
echo "  INFO Original file preserved"

# Step 3: Generate lock file and install base dependencies.
echo ""
echo "3 - Generating lock file and installing base dependencies..."

poetry env use python3

if [ -f "$POETRY_LOCK" ]; then
    rm -f "$POETRY_LOCK"
    echo "  OK Removed previous poetry.lock"
fi

poetry lock
poetry install

echo "  OK Base dependencies installed"

# Step 3b: Validate OpenCV installation.
echo ""
echo "3b - Checking OpenCV..."

set +e
poetry run python3 -c "import cv2; print(cv2.__version__)" >/dev/null 2>&1
CV2_STATUS=$?
set -e

if [ "$CV2_STATUS" -eq 0 ]; then
    echo "  OK OpenCV is already installed and importable"
else
    echo "  WARNING OpenCV could not be validated inside the Poetry environment"
    echo "  Reinstalling OpenCV manually..."
    poetry run pip install --force-reinstall --no-cache-dir opencv-python-headless==4.5.3.56
    echo "  OK OpenCV installed"
fi

# Step 4: Install PyTorch with CUDA 10.2 from NVIDIA wheel.
echo ""
echo "4 - Installing torch 1.10.0 with CUDA 10.2..."
echo "    NVIDIA wheel: torch-1.10.0-cp36-cp36m-linux_aarch64.whl"
echo ""

poetry run pip install "Cython<3"

TORCH_WHL="torch-1.10.0-cp36-cp36m-linux_aarch64.whl"
TORCH_URL="https://nvidia.box.com/shared/static/fjtbno0vpo676a25cgvuqc1wty0fkkg6.whl"

if poetry run python3 -c "import torch; print(torch.__version__)" 2>/dev/null | grep -q "1.10.0"; then
    echo "  OK torch 1.10.0 is already installed"
else
    wget -O "$TORCH_WHL" "$TORCH_URL"
    poetry run pip install --no-cache-dir "./$TORCH_WHL"
    rm -f "$TORCH_WHL"
    echo "  OK torch installed"
fi

# Step 5: Verify CUDA availability.
echo ""
echo "5 - Verifying CUDA..."

set +e
poetry run python3 -c "import torch; print(torch.__version__)" 2>/dev/null
TORCH_IMPORT=$?
set -e

if [ "$TORCH_IMPORT" -ne 0 ]; then
    echo "  ERROR Could not import torch"
    exit 1
fi

# Basic verification. This avoids unnecessary GPU calls before confirming torch import.
poetry run python3 << 'VERIFY'
import torch

print(f"OK torch:        {torch.__version__}")
print(f"OK CUDA:         {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"OK device:       {torch.cuda.get_device_name(0)}")

print("OK Setup verified")
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
echo "  To run the API in the background:"
echo "    nohup poetry run python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &"
echo ""
echo "  To test the API:"
echo "    curl http://localhost:8000/health"
echo ""
echo "=============================================="