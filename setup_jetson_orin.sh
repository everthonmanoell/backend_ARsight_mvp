#!/bin/bash

# Script de configuração automatica para Jetson AGX Orin
# Usa pyproject-jetson.toml como configuracao ativa
#
# COMO EXECUTAR (da raiz do projeto):
#   bash setup_jetson_orin.sh
#
# Este script:
# 1. Ativa o pyproject-jetson-orin.toml copiando para pyproject.toml
# 2. Reconstrói o poetry.lock para o ambiente Jetson Orin
# 3. Instala as dependencias do projeto com Poetry
# 4. Verifica versoes de torch e accelerate
# 5. Reinstala torch/accelerate apenas se necessario
# 6. Verifica disponibilidade de CUDA
#
# Requer:
# - Poetry instalado
# - Python compativel com o projeto
# - CUDA configurado na Jetson Orin
# - acesso ao indice Jetson AI Lab

set -e

TORCH_VERSION="2.8.0"
ACCELERATE_VERSION="1.2.1"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JETSON_TOML="$PROJECT_ROOT/pyproject-jetson-orin.toml"
PYPROJECT_TOML="$PROJECT_ROOT/pyproject.toml"
POETRY_LOCK="$PROJECT_ROOT/poetry.lock"

echo ""
echo "=============================================="
echo "Configuracao Jetson AGX Orin"
echo "=============================================="
echo "Diretorio: $PROJECT_ROOT"
echo ""

cd "$PROJECT_ROOT"

# Etapa 0: Verificar pre-requisitos
echo "0 - Verificando pre-requisitos..."
echo ""

if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "  OK Python: $PYTHON_VERSION"
else
    echo "  ERRO Python3 nao encontrado. Instale uma versao compativel."
    exit 1
fi

if command -v poetry >/dev/null 2>&1; then
    POETRY_VERSION=$(poetry --version 2>&1)
    echo "  OK Poetry: $POETRY_VERSION"
else
    echo "  ERRO Poetry nao encontrado. Instale antes de continuar."
    exit 1
fi

if command -v nvidia-smi >/dev/null 2>&1; then
    echo "  OK NVIDIA Driver: disponivel"
else
    echo "  AVISO nvidia-smi nao encontrado. Isso pode ser normal em alguns setups Jetson."
fi

# Etapa 1: Ativar configuracao Jetson Orin
echo ""
echo "1 - Copiando configuracao Jetson Orin..."

if [ ! -f "$JETSON_TOML" ]; then
    echo "  ERRO pyproject-jetson-orin.toml nao encontrado em:"
    echo "  $JETSON_TOML"
    exit 1
fi

cp "$JETSON_TOML" "$PYPROJECT_TOML"
echo "  OK Copiado pyproject-jetson-orin.toml para pyproject.toml"
echo "  INFO Arquivo original preservado (sem renomeacao)"

# Etapa 2: Reconstruir arquivo lock
echo ""
echo "2 - Reconstruindo poetry.lock para Jetson Orin..."

if [ -f "$POETRY_LOCK" ]; then
    rm -f "$POETRY_LOCK"
    echo "  OK Removido poetry.lock anterior"
fi

echo "  Rodando poetry lock..."
poetry lock
echo "  OK poetry.lock criado"

# Etapa 3: Instalar dependencias Poetry
echo ""
echo "3 - Instalando dependencias do projeto..."
echo "  Rodando poetry install..."
poetry install
echo "  OK Dependencias instaladas"

# Funcao para verificar versao de pacote dentro do ambiente Poetry
check_package_version() {
    local package_name="$1"

    poetry run python3 - <<PY 2>/dev/null || echo "NAO_INSTALADO"
try:
    import ${package_name}
    print(${package_name}.__version__)
except Exception:
    print("NAO_INSTALADO")
PY
}

# Etapa 4: Verificar versoes instaladas
echo ""
echo "4 - Verificando versoes instaladas..."

TORCH_INSTALLED=$(check_package_version "torch")
ACCELERATE_INSTALLED=$(check_package_version "accelerate")

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

# Etapa 5: Instalar/atualizar accelerate se necessario
echo ""
if [ "$NEED_ACCELERATE" = true ]; then
    echo "5 - Instalando accelerate $ACCELERATE_VERSION..."
    poetry run pip install --no-deps "accelerate==$ACCELERATE_VERSION"
    echo "  OK accelerate atualizado"
else
    echo "5 - accelerate ja esta na versao correta"
fi

# Etapa 6: Instalar/atualizar torch se necessario
echo ""
if [ "$NEED_TORCH" = true ]; then
    echo "6 - Instalando torch $TORCH_VERSION do Jetson AI Lab..."
    poetry run pip install --force-reinstall --no-cache-dir "torch==$TORCH_VERSION" \
        --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
    echo "  OK torch atualizado"
else
    echo "6 - torch ja esta na versao correta"
fi

# Etapa 7: Verificar instalacao final
echo ""
echo "7 - Verificando instalacao..."

poetry run python3 <<'VERIFY'
import sys
import torch
import accelerate

print(f"OK torch:        {torch.__version__}")
print(f"OK accelerate:   {accelerate.__version__}")
print(f"OK CUDA:         {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"OK Dispositivo:   {torch.cuda.get_device_name(0)}")
else:
    print("ERRO CUDA nao esta disponivel!")
    sys.exit(1)
VERIFY

echo ""
echo "=============================================="
echo "OK Configuracao concluida!"
echo "=============================================="
echo ""
echo "Proximos passos:"
echo ""
echo "  Para rodar a API REST:"
echo "    poetry run ar-api"
echo ""
echo "  Para executar o pipeline de teste:"
echo "    poetry run python tests/manual/test_pipeline.py"
echo ""
echo "  Para rodar testes unitarios:"
echo "    poetry run pytest tests/"
echo ""
echo "=============================================="