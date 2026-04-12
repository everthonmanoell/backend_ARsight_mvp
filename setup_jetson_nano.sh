#!/bin/bash

# Script de Configuração para Jetson Nano
# Instala PyTorch 1.10.0 com CUDA 10.2 (L4T R32.7.x - JetPack 4.6)
# usa --force-reinstall do Jetson AI Lab para garantir compatibilidade
# 
# Uso:
#   bash setup_jetson_nano.sh
#
# Este script:
# 1. Verifica as versões instaladas de torch
# 2. Instala/reinstala torch 1.10.0 com CUDA 10.2 via Jetson AI Lab index
# 3. Instala dependências Python
# 4. Verifica a disponibilidade de CUDA

set -e

TORCH_VERSION="1.10.0"
CUDA_VERSION="10.2"

echo ""
echo "🚀 Configuração Jetson Nano (L4T R32.7.x - JetPack 4.6)"
echo "=============================================="
echo "Python: $(python3 --version)"
echo "PyTorch alvo: $TORCH_VERSION com CUDA $CUDA_VERSION"
echo ""

# Etapa 0: Verificar versão do Python
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "0️⃣ Verificando Python..."
echo "  • Python $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" != "3.6" ]]; then
    echo "  ⚠️  Esperado Python 3.6 (jetson base image), encontrado $PYTHON_VERSION"
    echo "  ⚠️  Continuando mesmo assim..."
fi
echo ""

# Função para verificar se PyTorch está instalado com a versão correta
check_torch_version() {
    python3 -c "import torch; print(torch.__version__)" 2>/dev/null || echo "NÃO_INSTALADO"
}

# Etapa 1: Verificar versão atual de torch
echo "1️⃣ Verificando torch instalado..."
TORCH_INSTALLED=$(check_torch_version)

if [[ "$TORCH_INSTALLED" == *"$TORCH_VERSION"* ]]; then
    echo "  ✓ torch $TORCH_VERSION já está instalado"
    NEED_TORCH=false
else
    echo "  ✗ torch encontrado: $TORCH_INSTALLED"
    echo "  → Será reinstalado com --force-reinstall"
    NEED_TORCH=true
fi
echo ""

# Etapa 2: Instalar/atualizar torch do Jetson AI Lab
if $NEED_TORCH; then
    echo "2️⃣ Instalando torch $TORCH_VERSION+cu${CUDA_VERSION//./} do Jetson AI Lab..."
    echo "   (index: https://pypi.jetson-ai-lab.io)"
    echo ""
    
    # CRÍTICO: usar --index-url do Jetson AI Lab para aarch64
    # Isso garante que as wheels pré-compiladas com CUDA funcionem
    python3 -m pip install --force-reinstall --no-cache-dir \
        torch==$TORCH_VERSION \
        --index-url https://pypi.jetson-ai-lab.io/jp46/cu${CUDA_VERSION//./}
    
    echo ""
    echo "  ✓ torch instalado"
else
    echo "2️⃣ torch já está instalado ✓"
fi

echo ""

# Etapa 3: Instalar dependências do projeto
echo "3️⃣ Instalando dependências do projeto..."
python3 -m pip install --no-cache-dir -r requirements-jetson.txt

echo "  ✓ Dependências instaladas"
echo ""

# Etapa 4: Verificar instalação e CUDA
echo "4️⃣ Verificando instalação..."
python3 << 'VERIFY'
import torch
import sys

print(f"✓ torch versão: {torch.__version__}")
print(f"✓ CUDA versão: {torch.version.cuda}")

# CRÍTICO: Verificar se CUDA realmente está disponível
if torch.cuda.is_available():
    print(f"✓ CUDA disponível: SIM")
    print(f"✓ Dispositivo CUDA: {torch.cuda.get_device_name(0)}")
    print(f"✓ Compute capability: {torch.cuda.get_device_capability(0)}")
    
    # Teste simples de alocação de tensor em GPU
    try:
        test_tensor = torch.randn(10, 10).cuda()
        print(f"✓ Tensor em GPU: {test_tensor.device}")
        del test_tensor
        torch.cuda.empty_cache()
        print(f"✓ Teste GPU: PASSOU")
    except Exception as e:
        print(f"❌ Erro ao testar GPU: {e}")
        sys.exit(1)
else:
    print(f"❌ CUDA NÃO está disponível!")
    print(f"❌ Verifique se torch foi instalado da source correta")
    print(f"❌ Use: pip install --force-reinstall --no-cache-dir torch==1.10.0 --index-url https://pypi.jetson-ai-lab.io/jp46/cu102")
    sys.exit(1)

print("")
print("✅ Instalação VERIFICADA - CUDA funcionando!")
VERIFY

echo ""
echo "=============================================="
echo "✅ Configuração Jetson Nano concluída!"
echo ""
echo "PRÓXIMOS PASSOS:"
echo "  1. Rebuild container: docker-compose -f docker-compose-nano.yml build --no-cache"
echo "  2. Subir container: docker-compose -f docker-compose-nano.yml up -d"
echo "  3. Testar: curl http://localhost:8000/health"
echo "=============================================="
