#!/bin/bash

# Poetry Setup para Jetson Nano (sem Docker!)
# Instala e executa diretamente no Nano com Poetry
#
# Uso:
#   bash setup_poetry_nano.sh
#   poetry run python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000
#
# Este script:
# 1. Instala Poetry (se necessário)
# 2. Configura pyproject-jetson-nano.toml
# 3. Instala torch 1.10.0 com CUDA 10.2 via Jetson AI Lab
# 4. Instala dependências Python
# 5. Verifica CUDA

set -e

echo ""
echo "🚀 Poetry Setup para Jetson Nano (L4T R32.7 - JetPack 4.6)"
echo "=============================================="
echo ""

# Etapa 0: Verificar Python
echo "0️⃣ Verificando Python..."
PYTHON_VERSION=$(python3 --version 2>&1)
echo "  $PYTHON_VERSION"

if ! command -v poetry &> /dev/null; then
    echo ""
    echo "1️⃣ Instalando Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    echo "  ✓ Poetry instalado"
else
    echo ""
    echo "1️⃣ Poetry já instalado"
    poetry --version
fi

# Etapa 2: Preparar pyproject.toml
echo ""
echo "2️⃣ Configurando pyproject.toml..."

if [ -f "pyproject.toml" ]; then
    mv pyproject.toml pyproject-desktop.toml
    echo "  • Salvo: pyproject.toml → pyproject-desktop.toml"
fi

if [ -f "pyproject-jetson-nano.toml" ]; then
    cp pyproject-jetson-nano.toml pyproject.toml
    echo "  • Ativado: pyproject-jetson-nano.toml → pyproject.toml ✓"
else
    echo "  ❌ pyproject-jetson-nano.toml não encontrado!"
    exit 1
fi

# Etapa 3: Preparar ambiente Poetry
echo ""
echo "3️⃣ Criando environment Poetry..."
poetry env use python3
poetry install

# Etapa 4: Instalar torch com CUDA do Jetson AI Lab
echo ""
echo "4️⃣ Instalando torch 1.10.0 com CUDA 10.2..."
echo "   (via Jetson AI Lab index: https://pypi.jetson-ai-lab.io)"
echo ""

poetry run pip install --force-reinstall --no-cache-dir \
    torch==1.10.0 \
    --index-url https://pypi.jetson-ai-lab.io/jp46/cu102

echo "  ✓ torch instalado com CUDA"

# Etapa 5: Verificação CUDA
echo ""
echo "5️⃣ Verificando CUDA..."
poetry run python3 << 'VERIFY'
import torch

print(f"✓ torch versão: {torch.__version__}")
print(f"✓ CUDA versão: {torch.version.cuda}")

if torch.cuda.is_available():
    print(f"✓ CUDA disponível: SIM")
    print(f"✓ Dispositivo: {torch.cuda.get_device_name(0)}")
    
    # Teste rápido
    test = torch.randn(10, 10).cuda()
    print(f"✓ Tensor GPU: {test.device}")
    del test
    torch.cuda.empty_cache()
else:
    print(f"❌ CUDA NÃO disponível")
    exit(1)

print("")
print("✅ CUDA verificado!")
VERIFY

echo ""
echo "=============================================="
echo "✅ Setup completo!"
echo ""
echo "PRÓXIMOS PASSOS:"
echo ""
echo "1. Executar API:"
echo "   poetry run python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "2. Ou em background:"
echo "   nohup poetry run python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &"
echo ""
echo "3. Testar:"
echo "   curl http://localhost:8000/health"
echo ""
echo "=============================================="
