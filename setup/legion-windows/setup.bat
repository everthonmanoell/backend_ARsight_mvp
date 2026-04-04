@echo off
REM Script de configuracao para Desktop Legion (Windows - x86_64 com RTX)
REM Usa pyproject-legion.toml que inclui torch com CUDA 12.1+
REM 
REM Uso: setup.bat
REM Requer: Python 3.10+, Poetry, CUDA 12.1+

REM Se nao estiver na raiz do projeto, ir para raiz
if not exist "setup" (
    echo Erro: Execute este script da raiz do projeto
    echo Exemplo: cd %USERPROFILE%\TCC\backend_tcc_mvp
    echo.          setup\legion-windows\setup.bat
    exit /b 1
)

setlocal enabledelayedexpansion

color 0B
echo =====================================
echo Configuracao Desktop Legion (Windows)
echo =====================================
echo.

REM Etapa 0: Verificar pre-requisitos
echo Etapa 0: Verificando pre-requisitos...
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo XX Erro: Python nao encontrado. Instale Python 3.10+
    color 0B
    exit /b 1
) else (
    for /f "tokens=*" %%a in ('python --version 2^>^&1') do set PYTHON_VER=%%a
    echo.  OK: !PYTHON_VER!
)

poetry --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo XX Erro: Poetry nao encontrado. Instale com: pip install poetry
    color 0B
    exit /b 1
) else (
    for /f "tokens=*" %%a in ('poetry --version 2^>^&1') do set POETRY_VER=%%a
    echo.  OK: !POETRY_VER!
)

nvidia-smi >nul 2>&1
if %errorlevel% neq 0 (
    color 0E
    echo.  AVISO: nvidia-smi nao encontrado. Verifique drivers NVIDIA
    color 0B
) else (
    echo.  OK: NVIDIA Driver disponivel
)

cd ..\..\

REM Etapa 1: Alternar pyproject.toml
echo.
echo Etapa 1: Alternando para configuracao Legion...
if exist "pyproject.toml" (
    move /Y "pyproject.toml" "pyproject-jetson.toml" >nul
    echo.  OK: Salvou pyproject.toml como pyproject-jetson.toml
)

if not exist "pyproject-legion.toml" (
    color 0C
    echo XX Erro: pyproject-legion.toml nao encontrado!
    color 0B
    exit /b 1
)

move /Y "pyproject-legion.toml" "pyproject.toml" >nul
echo.  OK: Ativado pyproject-legion.toml

REM Etapa 2: Reconstruir arquivo lock
echo.
echo Etapa 2: Reconstruindo poetry.lock para Legion...
if exist "poetry.lock" (
    del /Q "poetry.lock"
    echo.  OK: Removido poetry.lock anterior
)

echo.  Rodando poetry lock... (pode levar alguns minutos)
call poetry lock
if %errorlevel% neq 0 (
    color 0C
    echo XX Erro ao executar poetry lock
    color 0B
    exit /b 1
)
echo.  OK: poetry.lock criado

REM Etapa 3: Instalar todas as dependencias
echo.
echo Etapa 3: Instalando dependencias (incluindo torch com CUDA 12.1+)...
echo.  Rodando poetry install... (pode levar alguns minutos)
call poetry install
if %errorlevel% neq 0 (
    color 0C
    echo XX Erro ao executar poetry install
    color 0B
    exit /b 1
)
echo.  OK: Dependencias instaladas

REM Etapa 4: Verificar instalacao
echo.
echo Etapa 4: Verificando instalacao...

call poetry run python -c "import torch; import transformers; import accelerate; print('OK torch:        ' + torch.__version__ + ' (CUDA: ' + str(torch.cuda.is_available()) + ')'); print('OK transformers: ' + transformers.__version__); print('OK accelerate:   ' + accelerate.__version__); import sys; sys.exit(0 if torch.cuda.is_available() else 1)"

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo XX Erro: CUDA nao disponivel
    color 0B
    echo.
    echo Dicas de solucao:
    echo.  1. Verifique nvidia-smi (deve mostrar CUDA 12.1+)
    echo.  2. Reinstale drivers NVIDIA (versao 550+)
    echo.  3. Reinstale PyTorch com CUDA explicitamente:
    echo.     poetry run pip install --force-reinstall torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    echo.
    echo.  Consulte setup\legion-windows\README.md para mais detalhes
    exit /b 1
)

echo.
echo =====================================
echo OK: Configuracao concluida!
echo =====================================
echo.
echo Proximos passos:
echo.
echo.  Para rodar a API REST:
echo.    poetry run ar-api
echo.
echo.  Para executar o pipeline de teste:
echo.    poetry run python tests/manual/test_pipeline.py
echo.
echo.  Para rodar testes unitarios:
echo.    poetry run pytest tests/
echo.
echo.  Documentacao disponivel em: setup\legion-windows\README.md
echo.
echo =====================================

color 07
