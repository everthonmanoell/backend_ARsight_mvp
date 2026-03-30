#!/bin/bash
# Setup script for Desktop Legion (x86_64 with RTX)
# Uses pyproject-legion.toml which includes torch

set -e

echo "====================================="
echo "Desktop Legion Setup"
echo "====================================="

# Step 1: Swap pyproject.toml
echo ""
echo "Step 1: Swapping to Legion configuration..."
if [ -f "pyproject.toml" ]; then
    mv pyproject.toml pyproject-jetson.toml
fi
if [ ! -f "pyproject-legion.toml" ]; then
    echo "❌ Error: pyproject-legion.toml not found!"
    exit 1
fi
mv pyproject-legion.toml pyproject.toml

# Step 2: Rebuild lock file
echo ""
echo "Step 2: Rebuilding poetry.lock for Legion..."
rm -f poetry.lock
poetry lock

# Step 3: Install all dependencies
echo ""
echo "Step 3: Installing all dependencies (including torch)..."
poetry install

# Step 4: Verify installation
echo ""
echo "Step 4: Verifying installation..."
poetry run python3 << 'VERIFY'
import torch
import transformers
import accelerate

print(f"✓ torch:        {torch.__version__} (CUDA: {torch.cuda.is_available()})")
print(f"✓ transformers: {transformers.__version__}")
print(f"✓ accelerate:   {accelerate.__version__}")

if not torch.cuda.is_available():
    print("⚠️  WARNING: CUDA not available!")
    exit(1)
VERIFY

echo ""
echo "====================================="
echo "✅ Setup complete!"
echo "====================================="
echo ""
echo "To switch back to Jetson:"
echo "  ./setup_jetson.sh"
