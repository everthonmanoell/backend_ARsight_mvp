#!/bin/bash
# Script de configuração para Desktop Legion (x86_64 com RTX)
# Usa pyproject-legion.toml que inclui torch

set -e

echo "====================================="
echo "Configuração Desktop Legion"
echo "====================================="

# Etapa 1: Alternar pyproject.toml
echo ""
echo "Etapa 1: Alternando para configuração Legion..."
if [ -f "pyproject.toml" ]; then
    mv pyproject.toml pyproject-jetson.toml
fi
if [ ! -f "pyproject-legion.toml" ]; then
    echo "❌ Erro: pyproject-legion.toml não encontrado!"
    exit 1
fi
mv pyproject-legion.toml pyproject.toml

# Etapa 2: Reconstruir arquivo lock
echo ""
echo "Etapa 2: Reconstruindo poetry.lock para Legion..."
rm -f poetry.lock
poetry lock

# Etapa 3: Instalar todas as dependências
echo ""
echo "Etapa 3: Instalando todas as dependências (incluindo torch)..."
poetry install

# Etapa 4: Verificar instalação
echo ""
echo "Etapa 4: Verificando instalação..."
poetry run python3 << 'VERIFY'
import torch
import transformers
import accelerate

print(f"✓ torch:        {torch.__version__} (CUDA: {torch.cuda.is_available()})")
print(f"✓ transformers: {transformers.__version__}")
print(f"✓ accelerate:   {accelerate.__version__}")

if not torch.cuda.is_available():
    print("⚠️  AVISO: CUDA não está disponível!")
    exit(1)
VERIFY

echo ""
echo "====================================="
echo "✅ Configuração concluída!"
echo "====================================="
echo ""
echo "Para voltar para Jetson:"
echo "  ./setup_jetson.sh"
