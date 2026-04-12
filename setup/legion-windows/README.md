# Setup Desktop Legion (Windows) — AR Diagnostic MVP

Guia completo para configurar o ambiente em PC Legion com Windows para usar CUDA 12.1+.

## ✅ Pré-requisitos

### Hardware
- NVIDIA GPU RTX 20 series ou mais novo (RTX 3080, 4090, etc.)
- Mínimo 6GB VRAM

### Software
- **Windows 10 ou 11**
- **Python 3.10+** → Download: https://www.python.org/downloads/
- **Poetry** → Install: `pip install poetry`
- **NVIDIA Drivers 550+** → Download: https://www.nvidia.com/Download/
- **Opcional: CUDA Toolkit 12.1** → Download: https://developer.nvidia.com/cuda-12-1-0-download-archive

---

## 🔍 Verificar Pré-requisitos

Abra PowerShell e execute:

```powershell
# Python
python --version
# Esperado: Python 3.10+

# Poetry
poetry --version
# Se não tiver: pip install poetry

# NVIDIA Driver
nvidia-smi
# Esperado: CUDA 12.1+
# Se não funcionar: instale drivers (Nvidia.com)
```

---

## 🚀 Setup Automático

### Executar o Script

**Opção 1: PowerShell (Recomendado)**
```powershell
cd C:\Users\<seu_usuario>\TCC\backend_tcc_mvp\setup\legion-windows
.\setup.ps1
```

**Opção 2: Command Prompt (cmd.exe)**
```cmd
cd C:\Users\<seu_usuario>\TCC\backend_tcc_mvp\setup\legion-windows
setup.bat
```

**Opção 3: De fora (PowerShell, da raiz)**
```powershell
cd C:\Users\<seu_usuario>\TCC\backend_tcc_mvp
.\setup\legion-windows\setup.ps1
```

⚠️ **IMPORTANTE (PowerShell):** Use `.\` antes do nome do script. PowerShell requer o prefixo por questões de segurança.

**O que o script faz:**

1. ✅ Verifica pré-requisitos (Python, Poetry, nvidia-smi)
2. ✅ Copia `pyproject-legion.toml` → `pyproject.toml` (sem renomear original)
3. ✅ Reconstrói `poetry.lock`
4. ✅ Instala todas as dependências (PyTorch com CUDA 12.1+)
5. ✅ Valida disponibilidade de CUDA

**Tempo esperado:** 5-10 minutos

### Se tiver erro PowerShell

**Erro:** `The term 'setup.ps1' is not recognized`

**Solução:** Execute este comando **uma vez**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Depois tente novamente:
```powershell
.\setup.ps1
```

Este comando permite que você execute scripts locais no PowerShell sem afetar a segurança do sistema.

---

## ⚙️ Setup Manual (passo a passo)

Se preferir fazer manualmente:

### Passo 1: Copiar config Legion
```powershell
# Copiar pyproject-legion.toml para usar como active
Copy-Item "pyproject-legion.toml" "pyproject.toml" -Force
```

### Passo 2: Instalar
```powershell
# Limpar lock anterior
Remove-Item poetry.lock -Force -ErrorAction SilentlyContinue

# Reconstruir
poetry lock
poetry install
```

### Passo 3: Validar
```powershell
poetry run python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'Device: {torch.cuda.get_device_name(0)}')
"
# Esperado: CUDA: True
```

---

## 🎯 Executar o Projeto

### API REST
```powershell
poetry run ar-api
```

Acesse: http://localhost:8000/docs (Swagger UI)

### Pipeline de Teste (True Batch)
```powershell
poetry run python tests/manual/test_pipeline.py
```

### Testes Unitários
```powershell
poetry run pytest tests/
```

---

## 🔧 Solução de Problemas Comuns

### ❌ CUDA não está disponível após setup

**Problema:** `torch.cuda.is_available()` retorna `False`

**Solução:**

1. **Verificar drivers NVIDIA:**
```powershell
nvidia-smi
# Se retornar erro: instale/atualize drivers de https://www.nvidia.com/Download/
```

2. **Reinstalar PyTorch com CUDA 12.1:**
```powershell
poetry run pip install --force-reinstall torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

3. **Limpar cache e tentar novamente:**
```powershell
poetry cache clear --all
Remove-Item poetry.lock -Force
poetry lock --no-cache --regenerate
poetry install
```

4. **Reiniciar Windows:**
   Às vezes driver precisa de reboot

---

### ❌ Script não executa

**Problema:** `cannot be loaded because running scripts is disabled`

**Solução:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Responda 'Y' se perguntado

.\setup\legion-windows\setup.ps1
```

---

### ❌ Poetry lock ou install falha

**Problema:** `error building wheel for ...`

**Solução:**
```powershell
# 1. Limpar cache
poetry cache clear --all

# 2. Reconstruir do zero
Remove-Item poetry.lock -Force
poetry lock --no-cache --regenerate

# 3. Instalar novamente
poetry install

# 4. Se ainda falhar, tente Python 3.10 (não 3.12+)
python --version  # Verifique versão
```

---

### ❌ Erro ao importar transformers ou accelerate

**Problema:** `ModuleNotFoundError: No module named 'transformers'`

**Solução:**
```powershell
# Garanta que poetry está usando o Python correto
poetry run python --version

# Reinstale dependências
poetry install --no-cache

# Se ainda falhar:
poetry run pip install transformers accelerate --upgrade
```

---

### ⚠️ CUDA Out of Memory

**Problema:** `RuntimeError: CUDA out of memory`

**Solução:**
- Reduza `batch_size` em `app/config/thresholds.yaml`
- Feche outras aplicações usando GPU
- Use Task Manager → Performance → GPU para monitorar uso

---

## 📊 Monitorar GPU

### Task Manager (integrado)
1. Abra Task Manager (Ctrl+Shift+Esc)
2. Abra abas "Desempenho" 
3. Clique em "GPU" (RTX 3080, RTX 4090, etc.)

Esperado durante execução: 50-80% utilização, VRAM 4-8GB

### nvidia-smi (linha de comando)
```powershell
# Uma vez
nvidia-smi

# Continuamente
while ($true) { nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader; Start-Sleep -Seconds 1 }
```

---

## 📁 Configuração

### Trocar Modelo LLM
Edite `app/config/config.yaml`:
```yaml
models:
  default: qwen    # ou 'phi'
  device: auto     # ou 'cuda', 'cpu'
  precision: auto  # ou 'fp32', 'fp16'
  use_4bit: true
```

---

## 🎓 Exemplos de Uso

### Upload de imagens
```powershell
curl -X POST http://localhost:8000/upload/batch `
  -F "files=@C:\path\to\image1.jpg" `
  -F "files=@C:\path\to\image2.jpg"
```

### Diagnóstico
```powershell
curl -X POST http://localhost:8000/diagnose/batch/batch_id_aqui
```

---

## 🔗 Links Úteis

- [NVIDIA Drivers](https://www.nvidia.com/Download/)
- [CUDA Toolkit 12.1](https://developer.nvidia.com/cuda-12-1-0-download-archive)
- [PyTorch Windows CUDA](https://pytorch.org/get-started/locally/)
- [NVIDIA CUDA Compute Capability](https://developer.nvidia.com/cuda-gpus)

---

## ❓ FAQ

**P: Preciso de cudnn?**
A: Não, PyTorch já vem com cuDNN otimizado.

**P: Qual CUDA devo instalar, 12.1 ou 12.6?**
A: Use drivers NVIDIA 550+. CUDA Toolkit é opcional. Se instalar, use 12.1.

**P: Posso usar GPU AMD ou Intel Arc?**
A: Não, este projeto usa CUDA (NVIDIA only).

**P: Como alternar entre Legion, Jetson e Nano?**
A: Copie o arquivo de configuração desejado:
```powershell
# Para Legion
Copy-Item pyproject-legion.toml pyproject.toml -Force

# Para Jetson Orin
Copy-Item pyproject-jetson.toml pyproject.toml -Force

# Para Jetson Nano
Copy-Item pyproject-jetson-nano.toml pyproject.toml -Force

# Depois, reconstrua e reinstale
poetry lock --no-cache --regenerate
poetry install
```

⚠️ **Nota:** Os arquivos `pyproject-*.toml` originais nunca são modificados, apenas copiado para `pyproject.toml`.

**P: Quanto de VRAM preciso?**
A: 
- Mínimo: 6GB (Phi-3 Mini)
- Recomendado: 10GB+ (RTX 3080 ou melhor)
- Ótimo: 24GB+ (RTX 4090)

---

## 📞 Suporte

Se tiver problemas:

1. Consulte [setup/TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
2. Execute novamente com saída de erro:
```powershell
poetry run python tests/manual/test_pipeline.py 2>&1 | head -30
```
3. Verifique [SETUP_INSTRUCTIONS.md](../../SETUP_INSTRUCTIONS.md)
