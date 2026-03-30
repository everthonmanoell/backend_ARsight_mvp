#!/bin/bash

# Setup Script for Jetson Orin
# Installs Poetry dependencies + Jetson-specific packages (torch, accelerate)
# Checks versions before installing to avoid unnecessary updates
# 
# Usage:
#   bash setup_jetson.sh
#
# This script:
# 1. Checks installed versions of torch and accelerate
# 2. Installs Poetry dependencies if needed
# 3. Installs/reinstalls torch and accelerate only if versions don't match
# 4. Verifies CUDA availability

set -e  # Exit on error

TORCH_VERSION="2.8.0"
ACCELERATE_VERSION="1.2.1"

echo ""
echo "🚀 Jetson Orin Setup"
echo "=============================================="

# Function to check if package is installed with correct version
check_package_version() {
    local package=$1
    local required_version=$2
    
    poetry run python3 -c "import $package; print($package.__version__)" 2>/dev/null || echo "NOT_INSTALLED"
}

# Step 0: Check current versions
echo ""
echo "0️⃣ Checking installed versions..."

TORCH_INSTALLED=$(check_package_version "torch" "$TORCH_VERSION")
ACCELERATE_INSTALLED=$(check_package_version "accelerate" "$ACCELERATE_VERSION")

echo "  • torch:      $TORCH_INSTALLED (required: $TORCH_VERSION)"
echo "  • accelerate: $ACCELERATE_INSTALLED (required: $ACCELERATE_VERSION)"

NEED_TORCH=false
NEED_ACCELERATE=false

if [ "$TORCH_INSTALLED" != "$TORCH_VERSION" ]; then
    NEED_TORCH=true
fi

if [ "$ACCELERATE_INSTALLED" != "$ACCELERATE_VERSION" ]; then
    NEED_ACCELERATE=true
fi

# Step 1: Poetry install
echo ""
echo "1️⃣ Installing Poetry dependencies..."
poetry install

# Step 2: Install/Update accelerate if needed
if $NEED_ACCELERATE; then
    echo ""
    echo "2️⃣ Installing accelerate $ACCELERATE_VERSION (--no-deps)..."
    poetry run pip install --no-deps accelerate==$ACCELERATE_VERSION
else
    echo ""
    echo "2️⃣ accelerate already installed ✓"
fi

# Step 3: Install/Update torch if needed
if $NEED_TORCH; then
    echo ""
    echo "3️⃣ Installing torch $TORCH_VERSION+cu126 from Jetson AI Lab..."
    poetry run pip install --force-reinstall --no-cache-dir torch==$TORCH_VERSION \
      --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
else
    echo ""
    echo "3️⃣ torch already installed ✓"
fi

# Step 4: Verify installation
echo ""
echo "4️⃣ Verifying installation..."
poetry run python3 << 'VERIFY'
import torch
import accelerate

print(f"✓ torch {torch.__version__}")
print(f"✓ accelerate {accelerate.__version__}")
print(f"✓ CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"✓ Device: {torch.cuda.get_device_name(0)}")
else:
    print("❌ CUDA NOT available!")
    exit(1)
VERIFY

echo ""
echo "=============================================="
echo "✅ Setup complete!"
echo ""
echo "Run pipeline:"
echo "  poetry run python tests/manual/test_pipeline.py"
echo "=============================================="
