# Script de configuração para Desktop Legion (Windows - x86_64 com RTX)
# Usa pyproject-legion.toml que inclui torch com CUDA 12.1+
# 
# COMO EXECUTAR:
#   De dentro da pasta setup/legion-windows/:
#     .\setup.ps1
#
#   Ou de fora (da raiz do projeto):
#     .\setup\legion-windows\setup.ps1
#
# ⚠️  IMPORTANTE: Use .\ antes do nome (required by PowerShell security policy)
#     Se receber erro "is not recognized", execute:
#     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#
# Requer: PowerShell 5.1+, Poetry, CUDA 12.1+, Python 3.10+

# Parar em qualquer erro
$ErrorActionPreference = "Stop"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Configuração Desktop Legion (Windows)" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Etapa 0: Verificar pré-requisitos
Write-Host "0️⃣  Verificando pré-requisitos..." -ForegroundColor Yellow
Write-Host ""

try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python: $pythonVersion"
}
catch {
    Write-Host "  ❌ Python não encontrado. Instale Python 3.10+" -ForegroundColor Red
    exit 1
}

try {
    $poetryVersion = poetry --version 2>&1
    Write-Host "  ✓ Poetry: $poetryVersion"
}
catch {
    Write-Host "  ❌ Poetry não encontrado. Instale com: pip install poetry" -ForegroundColor Red
    exit 1
}

try {
    $nvidiaCheck = nvidia-smi 2>&1
    Write-Host "  ✓ NVIDIA Driver: disponível"
}
catch {
    Write-Host "  ⚠️  nvidia-smi não encontrado. Verifique drivers NVIDIA" -ForegroundColor Yellow
}

# Etapa 1: Alternar pyproject.toml
Write-Host ""
Write-Host "1️⃣  Alternando para configuração Legion..." -ForegroundColor Yellow
if (Test-Path "pyproject.toml") {
    Move-Item "pyproject.toml" "pyproject-jetson.toml" -Force | Out-Null
    Write-Host "  ✓ Salvou pyproject.toml como pyproject-jetson.toml"
}

if (-not (Test-Path "pyproject-legion.toml")) {
    Write-Host "  ❌ Erro: pyproject-legion.toml não encontrado!" -ForegroundColor Red
    exit 1
}

Move-Item "pyproject-legion.toml" "pyproject.toml" -Force | Out-Null
Write-Host "  ✓ Ativado pyproject-legion.toml"

# Etapa 2: Reconstruir arquivo lock
Write-Host ""
Write-Host "2️⃣  Reconstruindo poetry.lock para Legion..." -ForegroundColor Yellow
if (Test-Path "poetry.lock") {
    Remove-Item "poetry.lock" -Force
    Write-Host "  ✓ Removido poetry.lock anterior"
}

Write-Host "  Rodando poetry lock... (pode levar alguns minutos)" -ForegroundColor Gray
poetry lock
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Erro ao executar poetry lock" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ poetry.lock criado"

# Etapa 3: Instalar todas as dependências
Write-Host ""
Write-Host "3️⃣  Instalando dependências (incluindo torch com CUDA 12.1+)..." -ForegroundColor Yellow
Write-Host "  Rodando poetry install... (pode levar alguns minutos)" -ForegroundColor Gray
poetry install
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Erro ao executar poetry install" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ Dependências instaladas"

# Etapa 4: Verificar instalação
Write-Host ""
Write-Host "4️⃣  Verificando instalação..." -ForegroundColor Yellow

$pythonCode = @'
import torch
import transformers
import accelerate

print(f"✓ torch:        {torch.__version__} (CUDA: {torch.cuda.is_available()})")
print(f"✓ transformers: {transformers.__version__}")
print(f"✓ accelerate:   {accelerate.__version__}")

if torch.cuda.is_available():
    print(f"✓ Dispositivo:   {torch.cuda.get_device_name(0)}")
else:
    print("⚠️  AVISO: CUDA não está disponível!")
    exit(1)
'@

poetry run python -c $pythonCode
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ Erro: CUDA não disponível" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Dicas de solução:" -ForegroundColor Yellow
    Write-Host "    1. Verifique nvidia-smi (deve mostrar CUDA 12.1+)"
    Write-Host "    2. Reinstale drivers NVIDIA (versão 550+)"
    Write-Host "    3. Reinstale PyTorch com CUDA explicitamente:"
    Write-Host "       poetry run pip install --force-reinstall torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
    Write-Host ""
    Write-Host "    Consulte setup/legion-windows/README.md para mais detalhes"
    exit 1
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "✅ Configuração concluída!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Para rodar a API REST:"
Write-Host "    poetry run ar-api"
Write-Host ""
Write-Host "  Para executar o pipeline de teste:"
Write-Host "    poetry run python tests/manual/test_pipeline.py"
Write-Host ""
Write-Host "  Para rodar testes unitários:"
Write-Host "    poetry run pytest tests/"
Write-Host ""
Write-Host "  Documentação disponível em: setup/legion-windows/README.md"
Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
