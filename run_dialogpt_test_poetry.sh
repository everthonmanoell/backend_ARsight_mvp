#!/bin/bash
# Test DialoGPT-small model on Jetson Nano via Poetry

set -e

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                   Testing DialoGPT-small on Jetson Nano                    ║"
echo "║                           Via Poetry Environment                           ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"

# Check if running on local machine
if [ "$HOSTNAME" != "jetson-nano" ] && [ "$HOSTNAME" != "jetson" ]; then
    echo ""
    echo "📍 Local environment detected. Will SSH to Jetson..."
    echo ""
    
    # Copy test script
    echo "📤 Copying test script to Jetson..."
    scp "$0" jetson:/tmp/test_dialogpt.sh 2>/dev/null || {
        echo "⚠️  Note: Using direct inline test"
    }
    
    # Run remotely
    ssh jetson << 'REMOTE_TEST'
#!/bin/bash
set -e

PROJECT_DIR=~/tcc/backend_tcc_mvp
cd "$PROJECT_DIR"

echo ""
echo "🔧 Setting up Poetry environment..."
if [ ! -f "~/.poetry/bin/poetry" ]; then
    echo "⚠️  Poetry not found at ~/.poetry/bin/poetry"
    echo "   Attempting to install from requirements-jetson-nano.txt instead..."
    pip3 install -r requirements-jetson-nano.txt --user
    echo ""
    echo "Running test with pip installed packages..."
    python3 test_dialogpt_nano.py
else
    echo "✅ Poetry found"
    source ~/.poetry/bin/env
    # Activate virtual env if needed
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    echo ""
    echo "📦 Installing dependencies..."
    poetry install --no-dev 2>&1 | grep -E "Installing|Up to date|Skipping" || true
    echo ""
    echo "🚀 Running test..."
    poetry run python test_dialogpt_nano.py
fi
REMOTE_TEST
    
    exit $?
fi

# Running on Jetson Nano
echo ""
echo "🎯 Running on Jetson Nano"
echo ""

PROJECT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$PROJECT_DIR"

echo "📂 Project: $PROJECT_DIR"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "🐍 Python: $PYTHON_VERSION"

# Check if Poetry is installed
if command -v poetry &> /dev/null; then
    echo "📦 Poetry: $(poetry --version)"
    echo ""
    echo "🔧 Setting up Poetry environment..."
    
    if [ ! -f ".venv/bin/python" ]; then
        echo "   Creating virtual environment..."
        poetry config virtualenvs.in-project true
        poetry install --no-dev 2>&1 | tail -5
    else
        echo "   ✅ Virtual environment exists"
    fi
    
    echo ""
    echo "🚀 Running test with Poetry..."
    poetry run python test_dialogpt_nano.py
    TEST_EXIT=$?
else
    echo "⚠️  Poetry not found, using pip packages..."
    echo ""
    echo "   Installing from requirements-jetson-nano.txt..."
    pip3 install -r requirements-jetson-nano.txt --upgrade 2>&1 | grep -E "Successfully|Requirement" || true
    
    echo ""
    echo "🚀 Running test..."
    python3 test_dialogpt_nano.py
    TEST_EXIT=$?
fi

echo ""
if [ $TEST_EXIT -eq 0 ]; then
    echo "✅ Test completed successfully!"
    echo ""
    echo "Next steps:"
    echo "  - Review the test output above"
    echo "  - If VRAM usage looks good, container is ready"
    echo "  - Check API at: curl -s http://localhost:8000/health | jq"
else
    echo "❌ Test failed with exit code: $TEST_EXIT"
fi

exit $TEST_EXIT
