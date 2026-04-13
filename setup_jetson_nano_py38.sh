#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Setup: Python 3.8 + PyTorch 1.11.0 + Qwen Stack para Jetson Nano
# ─────────────────────────────────────────────────────────────────────────────
# Uso: bash setup_jetson_nano_py38.sh

set -e

echo "🔧 Setup: Jetson Nano — Python 3.8 + PyTorch 1.11 + Qwen2.5-0.5B"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Verificar Python 3.8
echo "✓ Checking Python 3.8..."
if ! command -v python3.8 &> /dev/null; then
    echo "❌ Python 3.8 not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y python3.8 python3.8-dev python3.8-venv
fi
python3.8 --version

# 2. Criar venv com Python 3.8
echo ""
echo "✓ Setting up environment..."
if [ ! -d ".venv_py38" ]; then
    echo "Creating virtual environment..."
    python3.8 -m venv .venv_py38 || {
        echo "❌ venv creation failed. Trying alternative..."
        python3.8 -m pip install --user virtualenv
        python3.8 -m virtualenv .venv_py38
    }
    echo "Virtual environment created at .venv_py38"
fi

if [ ! -f ".venv_py38/bin/activate" ]; then
    echo "❌ Virtual environment activation script not found!"
    echo "Checking directory structure:"
    ls -la .venv_py38/ 2>/dev/null || echo "Directory empty or missing"
    exit 1
fi

source .venv_py38/bin/activate
echo "✅ Virtual environment activated"

# 3. Upgrade pip
echo ""
echo "✓ Upgrading pip..."
python3.8 -m pip install --upgrade pip setuptools wheel

# 4. Instalar PyTorch 1.11.0 para ARM64
# Referência: PyTorch wheels para Jetson em download.pytorch.org não têm ARM64
# Solução: usar o que compilou a comunidade ou construir localmente
echo ""
echo "✓ Installing PyTorch (ARM64 for Jetson Nano)..."

# Tentar diferentes versões em ordem de preferência
PYTORCH_INSTALLED=0

# Tentar 1.11.0 primeiro
echo "   Trying PyTorch 1.11.0..."
python3.8 -m pip install --no-cache-dir \
    torch==1.11.0 torchvision==0.12.0 \
    -f https://download.pytorch.org/whl/torch_stable.html 2>/dev/null && PYTORCH_INSTALLED=1

# Tentar 1.9.0 se 1.11 falhar
if [ $PYTORCH_INSTALLED -eq 0 ]; then
    echo "   Trying PyTorch 1.9.0..."
    python3.8 -m pip install --no-cache-dir \
        torch==1.9.0 torchvision==0.10.0 \
        -f https://download.pytorch.org/whl/torch_stable.html 2>/dev/null && PYTORCH_INSTALLED=1
fi

# Tentar versão latest do PyTorch
if [ $PYTORCH_INSTALLED -eq 0 ]; then
    echo "   Trying PyTorch latest (may not have CUDA support)..."
    python3.8 -m pip install --no-cache-dir torch torchvision 2>/dev/null && PYTORCH_INSTALLED=1
fi

if [ $PYTORCH_INSTALLED -eq 0 ]; then
    echo ""
    echo "❌ PyTorch installation failed for all versions."
    echo "   Jetson Nano ARM64 wheels podem não estar disponíveis."
    echo ""
    echo "Alternativas:"
    echo "   1. Compilar PyTorch localmente (2-3 horas)"
    echo "   2. Usar Docker com PyTorch pré-compilado"
    echo "   3. Manter Python 3.6 + DialoGPT (funciona 100%)"
    echo ""
    read -p "Continuar mesmo sem PyTorch? [s/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
else
    python3.8 -c "import torch; print(f'✅ PyTorch {torch.__version__} (CUDA: {torch.cuda.is_available()})')" || true
fi

# 5. Instalar Poetry (se ainda não instalado)
echo ""
echo "✓ Installing Poetry..."
if ! command -v poetry &> /dev/null; then
    curl -sSL https://install.python-poetry.org | python3.8 - 2>/dev/null || \
        echo "⚠️  Poetry installation via curl failed, trying pip..."
    python3.8 -m pip install --user poetry 2>/dev/null || \
        echo "⚠️  Poetry installation failed"
fi
export PATH="$HOME/.local/bin:$PATH"
poetry --version 2>/dev/null || echo "⚠️  Poetry not available, will use pip directly"

# 6. Instalar dependências com Poetry
echo ""
echo "✓ Installing dependencies..."

# Tentar com Poetry primeiro
if command -v poetry &> /dev/null; then
    echo "   Using Poetry..."
    poetry env use python3.8 2>/dev/null || true
    poetry install -vv --no-interaction \
        --with-all-groups \
        --from pyproject-jetson-nano-py38.toml 2>/dev/null && \
        echo "✅ Poetry install successful" || \
        echo "⚠️  Poetry install had issues, trying pip..."
fi

# Se Poetry falhou ou não está disponível, usar pip direto
if ! python3.8 -c "import fastapi" 2>/dev/null; then
    echo "   Using pip (fallback)..."
    python3.8 -m pip install --no-cache-dir -r requirements-jetson-py38.txt || \
        echo "❌ Pip install failed"
fi

# 7. Verificar instalação
echo ""
echo "✓ Verifying installation..."
python3.8 -c "import torch; print(f'✅ PyTorch {torch.__version__} (CUDA: {torch.cuda.is_available()})')" 2>/dev/null || \
    echo "⚠️  PyTorch not available (CPU mode)"
python3.8 -c "import transformers; print(f'✅ Transformers {transformers.__version__}')" 2>/dev/null || \
    echo "⚠️  Transformers not available"
python3.8 -c "import fastapi; print(f'✅ FastAPI {fastapi.__version__}')" 2>/dev/null || \
    echo "⚠️  FastAPI not available"

# 8. Criar script de startup
echo ""
echo "✓ Creating startup script..."
cat > start_py38.sh << 'EOF'
#!/bin/bash
source .venv_py38/bin/activate
export PATH="$HOME/.local/bin:$PATH"
poetry run ar-api --config pyproject-jetson-nano-py38.toml
EOF
chmod +x start_py38.sh

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Setup completo!"
echo ""
echo "📋 Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3.8 --version
[ -f ".venv_py38/bin/activate" ] && echo "✅ Virtual environment: .venv_py38" || echo "❌ Virtual environment: NOT FOUND"
python3.8 -c "import torch" 2>/dev/null && echo "✅ PyTorch: installed" || echo "⚠️  PyTorch: NOT installed (CPU fallback)"
python3.8 -c "import transformers" 2>/dev/null && echo "✅ Transformers: installed" || echo "❌ Transformers: NOT installed"
python3.8 -c "import fastapi" 2>/dev/null && echo "✅ FastAPI: installed" || echo "❌ FastAPI: NOT installed"
echo ""
echo "🚀 Para usar o novo stack Python 3.8:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  source .venv_py38/bin/activate"
echo "  poetry run ar-api"
echo ""
echo "Ou simplesmente:"
echo ""
echo "  bash start_py38.sh"
echo ""
echo "🔧 Se PyTorch não foi instalado:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Jetson Nano ARM64 wheels podem não estar em PyPI."
echo "   Opções:"
echo "   1. Usar Python 3.6 (DialoGPT funciona 100%)"
echo "   2. Docker com PyTorch pré-compilado"
echo "   3. Compilar PyTorch localmente (2-3 horas)"
echo ""
