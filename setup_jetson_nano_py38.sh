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

# 2. Criar venv com Python 3.8 (opcional, se usar Poetry com pyenv)
echo ""
echo "✓ Setting up environment..."
if [ ! -d ".venv_py38" ]; then
    python3.8 -m venv .venv_py38
    echo "Virtual environment created at .venv_py38"
fi
source .venv_py38/bin/activate

# 3. Upgrade pip
echo ""
echo "✓ Upgrading pip..."
python3.8 -m pip install --upgrade pip setuptools wheel

# 4. Instalar PyTorch 1.11.0 para ARM64
# Referência: PyTorch wheels para Jetson em download.pytorch.org não têm ARM64
# Solução: usar o que compilou a comunidade ou construir localmente
echo ""
echo "✓ Installing PyTorch 1.11.0 (ARM64 for Jetson Nano)..."
# Tentar do repositório de wheels pré-compilados
python3.8 -m pip install --no-cache-dir \
    torch==1.11.0 torchvision==0.12.0 \
    -f https://download.pytorch.org/whl/torch_stable.html || \
    echo "⚠️  PyTorch wheel not found in standard mirrors. Trying alternative..."

# Se falhar, tentar construir uma versão mais aceita
if ! python3.8 -c "import torch; print(f'PyTorch {torch.__version__}')"; then
    echo ""
    echo "❌ PyTorch 1.11 não disponível para ARM64. Alternativas:"
    echo "   1. Usar PyTorch 1.10 (pode estar em cache local)"
    echo "   2. Compilar PyTorch localmente (muito lento - 2-3 horas)"
    echo "   3. Usar Docker com wheel pré-compilada"
    echo ""
    echo "Tentando PyTorch 1.9.0 (mais compatível)..."
    python3.8 -m pip install --no-cache-dir \
        torch==1.9.0 torchvision==0.10.0 || \
        echo "⚠️  Todas as versões podem ter restrições ARM64. Verifique arquitetura."
fi

# 5. Instalar Poetry (se ainda não instalado)
echo ""
echo "✓ Installing Poetry..."
curl -sSL https://install.python-poetry.org | python3.8 - || true
export PATH="$HOME/.local/bin:$PATH"

# 6. Instalar dependências com Poetry
echo ""
echo "✓ Installing dependencies with Poetry..."
poetry env use python3.8 || true
poetry install -vv --no-interaction --with-all-groups \
    --from pyproject-jetson-nano-py38.toml || \
    echo "⚠️  Poetry install falhou. Tentando pip direto..."

# Fallback: pip direto
if ! poetry show > /dev/null 2>&1; then
    echo "Instalando com pip direto..."
    python3.8 -m pip install --no-cache-dir \
        fastapi==0.104.0 \
        uvicorn[standard]==0.24.0 \
        python-multipart==0.0.6 \
        pydantic==2.4.0 \
        pyyaml==6.0 \
        numpy==1.24.0 \
        pillow==10.0.0 \
        opencv-python-headless==4.8.0 \
        transformers==4.30.0 \
        huggingface-hub==0.14.0 \
        accelerate==0.27.0 \
        python-json-logger==2.0.7 \
        python-dotenv==1.0.0 \
        requests==2.31.0 \
        click==8.1.0
fi

# 7. Verificar instalação
echo ""
echo "✓ Verifying installation..."
python3.8 -c "import torch; print(f'✅ PyTorch {torch.__version__} (CUDA: {torch.cuda.is_available()})')"
python3.8 -c "import transformers; print(f'✅ Transformers {transformers.__version__}')"
python3.8 -c "import fastapi; print(f'✅ FastAPI {fastapi.__version__}')"

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
echo "Para usar o novo stack Python 3.8:"
echo ""
echo "  source .venv_py38/bin/activate"
echo "  poetry install --from pyproject-jetson-nano-py38.toml"
echo "  poetry run ar-api"
echo ""
echo "Ou simplesmente:"
echo ""
echo "  bash start_py38.sh"
echo ""
