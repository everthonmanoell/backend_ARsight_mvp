#!/usr/bin/env bash

# Automatic setup for any Ubuntu x86_64 desktop with an NVIDIA GPU.
# The PyTorch CUDA runtime is installed from the official cu128 index;
# a system-wide CUDA Toolkit is not required for this project.
#
# Run from the project root:
#   bash setup_desktop_gpu.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_TOML="$PROJECT_ROOT/pyproject-legion.toml"
PYPROJECT_TOML="$PROJECT_ROOT/pyproject.toml"
POETRY_LOCK="$PROJECT_ROOT/poetry.lock"

cd "$PROJECT_ROOT"

echo "=============================================="
echo "Desktop NVIDIA GPU Setup (Ubuntu)"
echo "=============================================="
echo "Project directory: $PROJECT_ROOT"
echo

echo "0 - Checking prerequisites..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found. Install Python 3.10 or newer."
    exit 1
fi
echo "  OK Python: $(python3 --version)"

if ! command -v poetry >/dev/null 2>&1; then
    echo "ERROR: Poetry not found. Install it before continuing."
    exit 1
fi
echo "  OK Poetry: $(poetry --version)"

if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "ERROR: nvidia-smi not found. Install or update the NVIDIA driver first."
    exit 1
fi
if ! nvidia-smi --query-gpu=name,driver_version --format=csv,noheader; then
    echo "ERROR: the NVIDIA driver could not access the GPU."
    exit 1
fi

echo
echo "1 - Activating the generic desktop NVIDIA configuration..."
if [[ ! -f "$DESKTOP_TOML" ]]; then
    echo "ERROR: $DESKTOP_TOML not found."
    exit 1
fi
cp "$DESKTOP_TOML" "$PYPROJECT_TOML"
echo "  OK Copied pyproject-legion.toml to pyproject.toml"

if [[ -f "$POETRY_LOCK" ]]; then
    rm -f "$POETRY_LOCK"
    echo "  OK Removed previous poetry.lock"
fi

echo
echo "2 - Resolving dependencies..."
poetry lock

echo
echo "3 - Installing dependencies..."
poetry install

echo
echo "4 - Verifying PyTorch CUDA..."
poetry run python - <<'PY'
import sys
import torch
import transformers
import accelerate

print(f"OK torch:        {torch.__version__}")
print(f"OK torch CUDA:   {torch.version.cuda}")
print(f"OK CUDA active:  {torch.cuda.is_available()}")
print(f"OK transformers: {transformers.__version__}")
print(f"OK accelerate:   {accelerate.__version__}")

if not torch.cuda.is_available():
    print("ERROR: PyTorch cannot access CUDA. Check the NVIDIA driver and environment.")
    sys.exit(1)

print(f"OK device:       {torch.cuda.get_device_name(0)}")
PY

echo
echo "=============================================="
echo "OK Generic NVIDIA GPU setup completed!"
echo "=============================================="
echo
echo "Start the API with:"
echo "  poetry run ar-api"
echo
echo "API documentation: http://localhost:8000/docs"
