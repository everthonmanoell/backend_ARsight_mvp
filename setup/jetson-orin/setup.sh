#!/bin/bash

# Script de Configuração para Jetson Orin
# Instala dependências Poetry + pacotes específicos da Jetson (torch, accelerate)
# Verifica versões antes de instalar para evitar atualizações desnecessárias
# 
# Uso:
#   cd ~backend_tcc_mvp
#   bash setup/jetson-orin/setup.sh
#
# Este script:
# 1. Verifica as versões instaladas de torch e accelerate
# 2. Instala dependências Poetry se necessário
# 3. Instala/reinstala torch e accelerate apenas se as versões não corresponderem
# 4. Verifica a disponibilidade de CUDA

set -e  # Sair em caso de erro

TORCH_VERSION="2.8.0"
ACCELERATE_VERSION="1.2.1"

echo ""
echo "🚀 Configuração Jetson Orin (JetPack 6.x)"
echo "=============================================="

# Função para verificar se o pacote está instalado com a versão correta
check_package_version() {
    local package=$1
    local required_version=$2
    
    poetry run python3 -c "import $package; print($package.__version__)" 2>/dev/null || echo "NÃO_INSTALADO"
}

# Etapa 0: Verificar versões atuais
echo ""
echo "0️⃣ Verificando versões instaladas..."

TORCH_INSTALLED=$(check_package_version "torch" "$TORCH_VERSION")
ACCELERATE_INSTALLED=$(check_package_version "accelerate" "$ACCELERATE_VERSION")

echo "  • torch:      $TORCH_INSTALLED (requerido: $TORCH_VERSION)"
echo "  • accelerate: $ACCELERATE_INSTALLED (requerido: $ACCELERATE_VERSION)"

NEED_TORCH=false
NEED_ACCELERATE=false

if [ "$TORCH_INSTALLED" != "$TORCH_VERSION" ]; then
    NEED_TORCH=true
fi

if [ "$ACCELERATE_INSTALLED" != "$ACCELERATE_VERSION" ]; then
    NEED_ACCELERATE=true
fi

# Etapa 1: Instalar dependências Poetry
echo ""
echo "1️⃣ Instalando dependências Poetry..."
poetry install

# Etapa 2: Instalar/atualizar accelerate se necessário
if $NEED_ACCELERATE; then
    echo ""
    echo "2️⃣ Instalando accelerate $ACCELERATE_VERSION (--no-deps)..."
    poetry run pip install --no-deps accelerate==$ACCELERATE_VERSION
else
    echo ""
    echo "2️⃣ accelerate já está instalado ✓"
fi

# Etapa 3: Instalar/atualizar torch se necessário
if $NEED_TORCH; then
    echo ""
    echo "3️⃣ Instalando torch $TORCH_VERSION+cu126 do Jetson AI Lab..."
    poetry run pip install --force-reinstall --no-cache-dir torch==$TORCH_VERSION \
      --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
else
    echo ""
    echo "3️⃣ torch já está instalado ✓"
fi

# Etapa 4: Verificar instalação
echo ""
echo "4️⃣ Verificando instalação..."
poetry run python3 << 'VERIFY'
import torch
import accelerate

print(f"✓ torch {torch.__version__}")
print(f"✓ accelerate {accelerate.__version__}")
print(f"✓ CUDA disponível: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"✓ Dispositivo: {torch.cuda.get_device_name(0)}")
else:
    print("❌ CUDA NÃO está disponível!")
    exit(1)
VERIFY

echo ""
echo "=============================================="
echo "✅ Configuração concluída!"
echo ""
echo "Execute o pipeline:"
echo "  poetry run python tests/manual/test_pipeline.py"
echo ""
echo "Ou inicie a API:"
echo "  poetry run ar-api"
echo "=============================================="
