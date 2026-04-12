# Script de configuracao automática para Desktop Legion (Windows - x86_64 com RTX)
# Usa pyproject-legion.toml que inclui torch com CUDA 12.1+
# 
# COMO EXECUTAR:
#   De dentro da pasta setup/legion-windows/:
#     .\setup.ps1
#
#   Ou de fora (da raiz do projeto):
#     .\setup\legion-windows\setup.ps1
#
# IMPORTANTE: Use .\ antes do nome (required by PowerShell security policy)
#     Se receber erro "is not recognized", execute:
#     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#
# Requer: PowerShell 5.1+, Poetry, CUDA 12.1+, Python 3.10+

# Parar em qualquer erro
$ErrorActionPreference = "Stop"

# Navegar para raiz do projeto
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $projectRoot

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Configuracao Desktop Legion (Windows)" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Diretorio: $projectRoot" -ForegroundColor Gray
Write-Host ""

# Etapa 0: Verificar pré-requisitos
Write-Host "0 - Verificando pre-requisitos..." -ForegroundColor Yellow
Write-Host ""

try {
    $pythonVersion = python --version 2>&1
    Write-Host "  OK Python: $pythonVersion"
}
catch {
    Write-Host "  ERRO Python nao encontrado. Instale Python 3.10+" -ForegroundColor Red
    exit 1
}

try {
    $poetryVersion = poetry --version 2>&1
    Write-Host "  OK Poetry: $poetryVersion"
}
catch {
    Write-Host "  ERRO Poetry nao encontrado. Instale com: pip install poetry" -ForegroundColor Red
    exit 1
}

try {
    $nvidiaCheck = nvidia-smi 2>&1
    Write-Host "  OK NVIDIA Driver: disponivel"
}
catch {
    Write-Host "  AVISO nvidia-smi nao encontrado. Verifique drivers NVIDIA" -ForegroundColor Yellow
}

# Etapa 1: Copiar configuracao Legion
Write-Host ""
Write-Host "1 - Copiando configuracao Legion..." -ForegroundColor Yellow

if (-not (Test-Path "pyproject-legion.toml")) {
    Write-Host "  ERRO pyproject-legion.toml nao encontrado!" -ForegroundColor Red
    exit 1
}

Copy-Item "pyproject-legion.toml" "pyproject.toml" -Force | Out-Null
Write-Host "  OK Copiado pyproject-legion.toml para pyproject.toml"
Write-Host "  INFO Arquivo original preservado (sem renomeacao)"

# Etapa 2: Reconstruir arquivo lock
Write-Host ""
Write-Host "2 - Reconstruindo poetry.lock para Legion..." -ForegroundColor Yellow
if (Test-Path "poetry.lock") {
    Remove-Item "poetry.lock" -Force
    Write-Host "  OK Removido poetry.lock anterior"
}

Write-Host "  Rodando poetry lock... (pode levar alguns minutos)" -ForegroundColor Gray
poetry lock
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERRO ao executar poetry lock" -ForegroundColor Red
    exit 1
}
Write-Host "  OK poetry.lock criado"

# Etapa 3: Instalar todas as dependencias
Write-Host ""
Write-Host "3 - Instalando dependencias (incluindo torch com CUDA 12.1+)..." -ForegroundColor Yellow
Write-Host "  Rodando poetry install... (pode levar alguns minutos)" -ForegroundColor Gray
poetry install
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERRO ao executar poetry install" -ForegroundColor Red
    exit 1
}
Write-Host "  OK Dependencias instaladas"

# Etapa 4: Verificar instalacao
Write-Host ""
Write-Host "4 - Verificando instalacao..." -ForegroundColor Yellow

$pythonCode = 'import torch
import transformers
import accelerate

print(f"OK torch:        {torch.__version__} (CUDA: {torch.cuda.is_available()})")
print(f"OK transformers: {transformers.__version__}")
print(f"OK accelerate:   {accelerate.__version__}")

if torch.cuda.is_available():
    print(f"OK Dispositivo:   {torch.cuda.get_device_name(0)}")
else:
    print("AVISO CUDA nao esta disponivel!")
    exit(1)'

poetry run python -c $pythonCode
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERRO CUDA nao disponivel" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Dicas de solucao:" -ForegroundColor Yellow
    Write-Host "    1. Verifique nvidia-smi (deve mostrar CUDA 12.1+)"
    Write-Host "    2. Reinstale drivers NVIDIA (versao 550+)"
    Write-Host "    3. Reinstale PyTorch com CUDA explicitamente:"
    Write-Host "       poetry run pip install --force-reinstall torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
    Write-Host ""
    Write-Host "    Consulte setup/legion-windows/README.md para mais detalhes"
    exit 1
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "OK Configuracao concluida!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Para rodar a API REST:"
Write-Host "    poetry run ar-api"
Write-Host ""
Write-Host "  Para executar o pipeline de teste:"
Write-Host "    poetry run python tests/manual/test_pipeline.py"
Write-Host ""
Write-Host "  Para rodar testes unitarios:"
Write-Host "    poetry run pytest tests/"
Write-Host ""
Write-Host "  Documentacao disponivel em: setup/legion-windows/README.md"
Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
