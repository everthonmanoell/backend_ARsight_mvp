#!/bin/bash

# Poetry Setup para Jetson Nano (sem Docker!)
# Instala e executa diretamente no Nano com Poetry
#
# Uso:
#   bash setup_poetry_nano.sh
#   poetry run python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000

set -e

# 🔧 FIX para Jetson Nano: OpenBLAS em ARMv8
# Sem isso, numpy/cv2/torch falham com "Illegal instruction"
export OPENBLAS_CORETYPE=ARMV8

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

# Garantir que o Poetry use python3
echo ""
echo "3️⃣ Gerando lock e instalando dependências base..."
poetry env use python3
rm -f poetry.lock
poetry lock
poetry install

# Etapa 3b: OpenCV manual (safe mode)
echo ""
echo "3b️⃣ Verificando OpenCV..."

set +e
poetry run python3 -c "import cv2; print(cv2.__version__)" >/dev/null 2>&1
CV2_STATUS=$?
set -e

if [ "$CV2_STATUS" -eq 0 ]; then
    echo "  • OpenCV já instalado ✓"
else
    echo "  • OpenCV não pôde ser validado no venv"
    echo "  • Reinstalando OpenCV manualmente..."
    poetry run pip install --force-reinstall --no-cache-dir opencv-python-headless==4.5.3.56
    echo "  ✓ OpenCV instalado"
fi

# Etapa 4: Instalar torch com CUDA via wheel direta
echo ""
echo "4️⃣ Instalando torch 1.10.0 com CUDA 10.2..."
echo "   (wheel NVIDIA direta: torch-1.10.0-cp36-cp36m-linux_aarch64.whl)"
echo ""

poetry run pip install 'Cython<3'

TORCH_WHL="torch-1.10.0-cp36-cp36m-linux_aarch64.whl"
TORCH_URL="https://nvidia.box.com/shared/static/fjtbno0vpo676a25cgvuqc1wty0fkkg6.whl"

if poetry run python3 -c "import torch; print(torch.__version__)" 2>/dev/null | grep -q "1.10.0"; then
    echo "  • torch 1.10.0 já instalado ✓"
else
    wget -O "$TORCH_WHL" "$TORCH_URL"
    poetry run pip install --no-cache-dir "./$TORCH_WHL"
    rm -f "$TORCH_WHL"
    echo "  ✓ torch instalado"
fi

# Etapa 5: Verificação CUDA (protegida contra Illegal instruction)
echo ""
echo "5️⃣ Verificando CUDA..."

set +e
poetry run python3 -c "import torch; print(torch.__version__)" 2>/dev/null
TORCH_IMPORT=$?
set -e

if [ "$TORCH_IMPORT" -ne 0 ]; then
    echo "❌ Não conseguiu importar torch"
    exit 1
fi

# Verificação básica (sem tentar acessar GPU ainda, que pode dar Illegal instruction)
poetry run python3 << 'VERIFY'
import torch
print(f"✓ torch versão: {torch.__version__}")
print(f"✓ CUDA disponível: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"✓ Dispositivo: {torch.cuda.get_device_name(0)}")
print("✅ Setup verificado!")
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
