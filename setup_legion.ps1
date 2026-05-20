# Automatic setup script for Desktop Legion (Windows x86_64 with NVIDIA RTX)
# Uses pyproject-legion.toml, which includes PyTorch with CUDA 12.1+ support.
#
# HOW TO RUN from the project root:
#   .\setup_legion.ps1
#
# If PowerShell blocks script execution, run first:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#
# Requirements: PowerShell 5.1+, Poetry, CUDA 12.1+, Python 3.10+

# Stop on any error.
$ErrorActionPreference = "Stop"

# Navigate to the project root.
# Since this script is stored in the project root, use the directory where it is located.
$projectRoot = $PSScriptRoot

if (-not $projectRoot -or $projectRoot -eq "") {
    $projectRoot = (Get-Location).Path
}

Set-Location $projectRoot

# Absolute paths to avoid directory-related issues.
$legionToml = Join-Path $projectRoot "pyproject-legion.toml"
$pyprojectToml = Join-Path $projectRoot "pyproject.toml"
$poetryLock = Join-Path $projectRoot "poetry.lock"
$readmePath = Join-Path $projectRoot "setup\legion-windows\README.md"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Desktop Legion Setup (Windows)" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Project directory: $projectRoot" -ForegroundColor Gray
Write-Host ""

# Step 0: Check prerequisites.
Write-Host "0 - Checking prerequisites..." -ForegroundColor Yellow
Write-Host ""

try {
    $pythonVersion = python --version 2>&1
    Write-Host "  OK Python: $pythonVersion"
}
catch {
    Write-Host "  ERROR Python not found. Install Python 3.10+." -ForegroundColor Red
    exit 1
}

try {
    $poetryVersion = poetry --version 2>&1
    Write-Host "  OK Poetry: $poetryVersion"
}
catch {
    Write-Host "  ERROR Poetry not found. Install it with: pip install poetry" -ForegroundColor Red
    exit 1
}

try {
    $null = nvidia-smi 2>&1
    Write-Host "  OK NVIDIA driver: available"
}
catch {
    Write-Host "  WARNING nvidia-smi not found. Check NVIDIA drivers." -ForegroundColor Yellow
}

# Step 1: Copy the Legion-specific configuration.
Write-Host ""
Write-Host "1 - Copying Desktop Legion configuration..." -ForegroundColor Yellow

if (-not (Test-Path $legionToml)) {
    Write-Host "  ERROR pyproject-legion.toml not found at:" -ForegroundColor Red
    Write-Host "  $legionToml" -ForegroundColor Red
    exit 1
}

Copy-Item $legionToml $pyprojectToml -Force | Out-Null
Write-Host "  OK Copied pyproject-legion.toml to pyproject.toml"
Write-Host "  INFO Original file preserved"

# Step 2: Rebuild the lock file.
Write-Host ""
Write-Host "2 - Rebuilding poetry.lock for Desktop Legion..." -ForegroundColor Yellow

if (Test-Path $poetryLock) {
    Remove-Item $poetryLock -Force
    Write-Host "  OK Removed previous poetry.lock"
}

Write-Host "  Running poetry lock... This may take a few minutes." -ForegroundColor Gray
poetry lock

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR while running poetry lock" -ForegroundColor Red
    exit 1
}

Write-Host "  OK poetry.lock created"

# Step 3: Install dependencies.
Write-Host ""
Write-Host "3 - Installing dependencies, including PyTorch with CUDA 12.1+..." -ForegroundColor Yellow
Write-Host "  Running poetry install... This may take a few minutes." -ForegroundColor Gray

poetry install

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR while running poetry install" -ForegroundColor Red
    exit 1
}

Write-Host "  OK Dependencies installed"

# Step 4: Verify installation.
Write-Host ""
Write-Host "4 - Verifying installation..." -ForegroundColor Yellow

$pythonCode = @'
import sys
import torch
import transformers
import accelerate

print(f"OK torch:        {torch.__version__} (CUDA: {torch.cuda.is_available()})")
print(f"OK transformers: {transformers.__version__}")
print(f"OK accelerate:   {accelerate.__version__}")

if torch.cuda.is_available():
    print(f"OK device:       {torch.cuda.get_device_name(0)}")
else:
    print("WARNING CUDA is not available.")
    sys.exit(1)
'@

poetry run python -c $pythonCode

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR CUDA is not available" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "    1. Check nvidia-smi. It should report CUDA 12.1+."
    Write-Host "    2. Reinstall NVIDIA drivers, preferably version 550+."
    Write-Host "    3. Reinstall PyTorch with CUDA explicitly:"
    Write-Host "       poetry run pip install --force-reinstall torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
    Write-Host ""

    if (Test-Path $readmePath) {
        Write-Host "    See $readmePath for more details."
    }

    exit 1
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "OK Setup completed successfully!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  To run the REST API:"
Write-Host "    poetry run ar-api"
Write-Host ""
Write-Host "  To run the manual pipeline test:"
Write-Host "    poetry run python tests/manual/test_pipeline.py"
Write-Host ""
Write-Host "  To run unit tests:"
Write-Host "    poetry run pytest tests/"
Write-Host ""

if (Test-Path $readmePath) {
    Write-Host "  Documentation available at: $readmePath"
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green