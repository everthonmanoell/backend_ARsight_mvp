# Script de configuração para Desktop Legion (Windows - x86_64 com RTX)
# Usa pyproject-legion.toml que inclui torch com CUDA 12.1+
# 
# Uso: .\setup_legion.ps1
# Requer: PowerShell 5.1+, Poetry, CUDA 12.1+

# Parar em qualquer erro
$ErrorActionPreference = "Stop"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Configuração Desktop Legion (Windows)" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Etapa 1: Alternar pyproject.toml
Write-Host "Etapa 1: Alternando para configuração Legion..." -ForegroundColor Yellow
if (Test-Path "pyproject.toml") {
    Move-Item "pyproject.toml" "pyproject-jetson.toml" -Force | Out-Null
    Write-Host "  ✓ Salvou pyproject.toml como pyproject-jetson.toml"
}

if (-not (Test-Path "pyproject-legion.toml")) {
    Write-Host "❌ Erro: pyproject-legion.toml não encontrado!" -ForegroundColor Red
    exit 1
}

Move-Item "pyproject-legion.toml" "pyproject.toml" -Force | Out-Null
Write-Host "  ✓ Ativado pyproject-legion.toml"

# Etapa 2: Reconstruir arquivo lock
Write-Host ""
Write-Host "Etapa 2: Reconstruindo poetry.lock para Legion..." -ForegroundColor Yellow
if (Test-Path "poetry.lock") {
    Remove-Item "poetry.lock" -Force
    Write-Host "  ✓ Removido poetry.lock anterior"
}

Write-Host "  Rodando poetry lock..." -ForegroundColor Gray
poetry lock
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao executar poetry lock" -ForegroundColor Red
    exit 1
}

# Etapa 3: Instalar todas as dependências
Write-Host ""
Write-Host "Etapa 3: Instalando todas as dependências (incluindo torch com CUDA)..." -ForegroundColor Yellow
Write-Host "  Rodando poetry install..." -ForegroundColor Gray
poetry install
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao executar poetry install" -ForegroundColor Red
    exit 1
}

# Etapa 4: Verificar instalação
Write-Host ""
Write-Host "Etapa 4: Verificando instalação..." -ForegroundColor Yellow

$pythonCode = @"
import torch
import transformers
import accelerate

print(f"✓ torch:        {torch.__version__} (CUDA: {torch.cuda.is_available()})")
print(f"✓ transformers: {transformers.__version__}")
print(f"✓ accelerate:   {accelerate.__version__}")

if not torch.cuda.is_available():
    print("⚠️  AVISO: CUDA não está disponível!")
    exit(1)
"@

poetry run python -c $pythonCode
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro na verificação de CUDA" -ForegroundColor Red
    Write-Host ""
    Write-Host "Dicas de solução:" -ForegroundColor Yellow
    Write-Host "  1. Verifique nvidia-smi (deve mostrar CUDA 12.1+)"
    Write-Host "  2. Reinstale PyTorch com:"
    Write-Host "     poetry run pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
    exit 1
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "✅ Configuração concluída!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Para rodar a API:" -ForegroundColor Cyan
Write-Host "  poetry run ar-api"
Write-Host ""
Write-Host "Para voltar para Jetson:" -ForegroundColor Cyan
Write-Host "  bash setup_jetson.sh"
Write-Host ""
