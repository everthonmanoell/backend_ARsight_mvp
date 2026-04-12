#!/bin/bash

# Poetry Setup para Jetson Nano (sem Docker)
# JetPack 4.6 / L4T R32.7.x / Python 3.6.9
#
# Este script:
# 1. Garante Poetry
# 2. Ativa o pyproject específico da Nano
# 3. Instala dependências base com Poetry
# 4. Instala OpenCV manualmente
# 5. Instala torch manualmente via wheel local/NVIDIA
# 6. Valida numpy, cv2, torch e CUDA

set -e

# CRÍTICO para evitar Illegal instruction com numpy/torch/cv2
export OPENBLAS_CORETYPE=ARMV8

echo ""
echo "🚀 Poetry Setup para Jetson Nano (L4T R32.7 - JetPack 4.6)"
echo "=============================================="
echo ""

echo "0️⃣ Verificando Python..."
python3 --version

if ! command -v poetry >/dev/null 2>&1; then
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

echo ""
echo "3️⃣ Gerando lock e instalando dependências base..."
poetry env use python3
rm -f poetry.lock
poetry lock
poetry install

echo ""
echo "3b️⃣ Instalando OpenCV manualmente..."
poetry run pip install --force-reinstall --no-cache-dir opencv-python-headless==4.5.3.56
echo "  ✓ OpenCV instalado"

echo ""
echo "4️⃣ Instalando torch 1.10.0 com CUDA 10.2..."
echo "   (wheel NVIDIA direta: torch-1.10.0-cp36-cp36m-linux_aarch64.whl)"
echo ""

poetry run pip uninstall -y torch || true
poetry run pip uninstall -y torch || true

poetry run pip install 'Cython<3'

TORCH_WHL="torch-1.10.0-cp36-cp36m-linux_aarch64.whl"
TORCH_URL="https://nvidia.box.com/shared/static/fjtbno0vpo676a25cgvuqc1wty0fkkg6.whl"

if [ ! -f "$TORCH_WHL" ]; then
    wget -O "$TORCH_WHL" "$TORCH_URL"
fi

poetry run pip install --force-reinstall --no-deps "./$TORCH_WHL"
echo "  ✓ torch instalado"

echo ""
echo "5️⃣ Verificando ambiente..."
poetry run python3 << 'VERIFY'
import numpy
import cv2
import torch

print(f"✓ numpy: {numpy.__version__}")
print(f"✓ cv2: {cv2.__version__}")
print(f"✓ torch: {torch.__version__}")
print(f"✓ CUDA disponível: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"✓ Dispositivo: {torch.cuda.get_device_name(0)}")
    x = torch.randn(4, 4).cuda()
    print(f"✓ Tensor GPU: {x.device}")
else:
    raise SystemExit("❌ CUDA não disponível")

print("")
print("✅ Setup verificado!")
VERIFY

echo ""
echo "=============================================="
echo "✅ Setup completo da Nano!"
echo ""
echo "IMPORTANTE:"
echo "  export OPENBLAS_CORETYPE=ARMV8"
echo ""
echo "Para persistir:"
echo "  echo 'export OPENBLAS_CORETYPE=ARMV8' >> ~/.bashrc"
echo ""
echo "Executar API:"
echo "  poetry run ar-api"
echo ""
echo "=============================================="