#!/bin/bash
# Install Poetry on Jetson Nano (Python 3.6)

set -e

echo "=== Installing Poetry on Jetson Nano ==="
echo ""

# Update pip first
echo "📦 Updating pip..."
pip3 install --upgrade pip setuptools wheel

# Install Poetry 1.1.x (compatible with Python 3.6)
echo "🎼 Installing Poetry 1.1.x (for Python 3.6)..."
pip3 install poetry==1.1.15

# Add Poetry to PATH
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
echo ""
echo "✅ Poetry installed. Verifying..."
poetry --version

# Configure Poetry for this project
echo ""
echo "⚙️  Configuring Poetry..."
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true
# Note: virtualenvs.prefer-active-python not available in Poetry 1.1

echo ""
echo "✅ Poetry installation complete!"
echo ""
echo "📝 Next steps:"
echo "  1. cd ~/tcc/backend_tcc_mvp"
echo "  2. bash setup_poetry_nano.sh"
echo ""
