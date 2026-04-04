@echo off
REM Script de configuracao para Desktop Legion (Windows - x86_64 com RTX)
REM Usa pyproject-legion.toml que inclui torch com CUDA 12.1+
REM 
REM Uso: setup_legion.bat
REM Requer: Poetry, CUDA 12.1+

setlocal enabledelayedexpansion

color 0B
echo =====================================
echo Configuracao Desktop Legion (Windows)
echo =====================================
echo.

REM Etapa 1: Alternar pyproject.toml
echo Etapa 1: Alternando para configuracao Legion...
if exist pyproject.toml (
    ren pyproject.toml pyproject-jetson.toml
    echo.  OK: Salvou pyproject.toml como pyproject-jetson.toml
)

if not exist pyproject-legion.toml (
    color 0C
    echo XX Erro: pyproject-legion.toml nao encontrado!
    color 0B
    exit /b 1
)

ren pyproject-legion.toml pyproject.toml
echo.  OK: Ativado pyproject-legion.toml

REM Etapa 2: Reconstruir arquivo lock
echo.
echo Etapa 2: Reconstruindo poetry.lock para Legion...
if exist poetry.lock (
    del poetry.lock
    echo.  OK: Removido poetry.lock anterior
)

echo.  Rodando poetry lock...
call poetry lock
if %errorlevel% neq 0 (
    color 0C
    echo XX Erro ao executar poetry lock
    color 0B
    exit /b 1
)

REM Etapa 3: Instalar todas as dependencias
echo.
echo Etapa 3: Instalando todas as dependencias ^(incluindo torch com CUDA^)...
echo.  Rodando poetry install...
call poetry install
if %errorlevel% neq 0 (
    color 0C
    echo XX Erro ao executar poetry install
    color 0B
    exit /b 1
)

REM Etapa 4: Verificar instalacao
echo.
echo Etapa 4: Verificando instalacao...
call poetry run python -c "import torch; import transformers; import accelerate; print(f'OK torch:        {torch.__version__} (CUDA: {torch.cuda.is_available()})'); print(f'OK transformers: {transformers.__version__}'); print(f'OK accelerate:   {accelerate.__version__}'); exit(1 if not torch.cuda.is_available() else 0)"

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo XX Erro na verificacao de CUDA
    color 0B
    echo.
    echo Dicas de solucao:
    echo.  1. Verifique nvidia-smi ^(deve mostrar CUDA 12.1+^)
    echo.  2. Reinstale PyTorch com:
    echo.     poetry run pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    exit /b 1
)

echo.
echo =====================================
echo OK: Configuracao concluida!
echo =====================================
echo.
echo Para rodar a API:
echo.  poetry run ar-api
echo.
echo Para voltar para Jetson:
echo.  bash setup_jetson.sh
echo.

color 07
