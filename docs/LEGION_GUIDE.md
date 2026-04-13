# Legion Desktop Setup & Deployment Guide

Guia completo para setup e deploy no **PC Legion com Windows + RTX**.

> **Recomendação:** Usar **Phi-3-mini** para melhor qualidade. Alternativa: **Qwen2.5-0.5B** para mais velocidade. Ver [MODEL_SELECTION.md](MODEL_SELECTION.md).

## ✅ Hardware Verificado

| Item | Versão | Status |
|---|---|---|
| **PC Legion** | Desktop | ✅ Testado |
| **GPU** | RTX 3080 (10GB VRAM) | ✅ Testado |
| **Windows** | 11 | ✅ Compatível |
| **CUDA** | 12.1+ | ✅ Funciona |
| **Python** | 3.10+ | ✅ Recomendado |
| **PyTorch** | 2.0+ | ✅ Suporta CUDA 12.1 |

---

## 📋 Pré-requisitos

### 1. NVIDIA Driver (Versão 550+)

1. Baixar em [NVIDIA Driver Download](https://www.nvidia.com/Download/driverDetails.aspx/)
2. Selecionar GPU RTX
3. Download versão 550+ para suportar CUDA 12.1
4. Instalar e **reiniciar**

Verificar:
```powershell
nvidia-smi
# Deve mostrar GPU, driver 550+, CUDA 12.1
```

### 2. CUDA Toolkit 12.1 (Opcional)

Se `nvidia-smi` não mostrar CUDA:

1. Download [CUDA 12.1 Toolkit](https://developer.nvidia.com/cuda-12-1-0-download-archive)
2. Escolher: Windows → 11 → x86_64 → exe (local)
3. Instalar
4. Reiniciar

### 3. Python 3.10+

```powershell
python --version  # Esperado: 3.10.x ou 3.11.x
```

### 4. Poetry

```powershell
pip install poetry
poetry --version
```

---

## 🚀 Setup com Script Automatizado (Recomendado)

### Windows PowerShell

```powershell
cd backend_tcc_mvp
.\setup_legion.ps1
```

O script fará:
- ✅ Validar Python + Poetry + CUDA
- ✅ Copiar `pyproject-legion.toml` para `pyproject.toml`
- ✅ Rebuild `poetry.lock` para RTX
- ✅ Instalar PyTorch com CUDA 12.1
- ✅ Validar GPU disponível

Se houver erro de policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup_legion.ps1
```

---

## 🚀 Setup Manual

### 1. Copiar Configuration

```powershell
cd backend_tcc_mvp

# Ativar configuração Legion (com CUDA 12.1 + Phi-3)
Copy-Item pyproject-legion.toml pyproject.toml -Force
```

### 2. Instalar Dependências

```powershell
# Remover lock anterior
Remove-Item poetry.lock -Force -ErrorAction SilentlyContinue

# Rebuild lock
poetry lock

# Instalar (inclui PyTorch com CUDA 12.1)
poetry install
```

Tempo estimado: 5-10 minutos (PyTorch download ~2GB)

### 3. Verificar CUDA

```powershell
poetry run python -c "
import torch
print(f'✅ PyTorch {torch.__version__}')
print(f'✅ CUDA: {torch.cuda.is_available()}')
print(f'✅ GPU: {torch.cuda.get_device_name(0)}')
if not torch.cuda.is_available():
    exit(1)
"
```

---

## ⚙️ Configuração (YAML)

### Recomendação: Phi-3-mini

```yaml
models:
  default: phi               # Excelente qualidade, ~300 ms
  device: cuda
  precision: fp16
  use_4bit: false            # RTX 3080 tem espaço, não necessário

phi_config:
  model_name: "microsoft/Phi-3-mini-4k-instruct"
  prompt_max_length: 256
  max_tokens: 32
  summary_max_tokens: 64
  temperature: 0.7
  top_p: 0.95
  greedy_decoding: false
```

### Alternativa: Qwen2.5-0.5B (mais rápido)

```yaml
models:
  default: qwen              # Qualidade boa, ~100 ms
  device: cuda
  precision: fp16

qwen_config:
  model_path: "Qwen/Qwen2.5-0.5B-Instruct"  # Download automático
  prompt_max_length: 128
  max_tokens: 20
  summary_max_tokens: 32
  temperature: 0.2
  top_p: 0.9
```

### DialoGPT (ultrarrápido)

```yaml
models:
  default: dialogpt          # ~50 ms, qualidade aceitável
  device: cuda
  precision: fp16
```

---

## 🏃 Executar API

### Opção 1: Poetry (Desenvolvimento)

```powershell
poetry run ar-api
# Acessa em: http://localhost:8000
```

### Opção 2: Docker (Produção)

```powershell
# Build
docker build -t ar-diagnostic-mvp:legion .

# Run
docker run --rm `
  --gpus all `
  -p 8000:8000 `
  -v $(Get-Location)\data:/app/data `
  -v $(Get-Location)\logs:/app/logs `
  ar-diagnostic-mvp:legion
```

### Opção 3: Docker Compose

```powershell
docker-compose up -d

# Logs
docker-compose logs -f

# Parar
docker-compose down
```

---

## 🧪 Validação

### 1. API Health

```powershell
curl http://localhost:8000/health
# Esperado: {"status":"healthy"}
```

### 2. Teste com Imagem

```powershell
# Preparar imagem
cp data\illumination\normal\sample.jpg .\test.jpg

# Enviar
curl -X POST http://localhost:8000/diagnose `
  -F "file=@test.jpg" `
  -F "frame_index=0"

# Esperado: JSON com diagnosis
```

### 3. Benchmark de Performance

```powershell
poetry run python -c "
import torch
import time

# Teste GPU performance
x = torch.randn(1000, 1000).cuda()
y = torch.randn(1000, 1000).cuda()

torch.cuda.synchronize()
start = time.time()
z = torch.matmul(x, y)
torch.cuda.synchronize()
elapsed = time.time() - start

print(f'✅ GPU performance: {1/elapsed:.0f} ops/sec')
print(f'✅ GPU memory: {torch.cuda.memory_allocated() / 1e9:.1f} GB')
"
```

---

## 📊 Performance Esperada

**Legion RTX 3080:**

| Modelo | Latência | VRAM | Status |
|---|---|---|---|
| DialoGPT | ~50 ms/frame | 500 MB | ✅ Ultrarrápido |
| Qwen 0.5B | ~100 ms/frame | 1.5 GB | ✅ Excelente |
| Phi-3-mini | ~300 ms/frame | 7.6 GB | ✅ Recomendado |

**Tempo total (batch 10 frames):**
- DialoGPT: ~1.5s ✅
- Qwen: ~2s ✅
- Phi-3: ~3-4s ✅

---

## 🛠️ Troubleshooting

### Erro: `nvidia-smi` não encontrado

```powershell
# Verificar PATH do sistema
$env:PATH

# Se não tiver NVIDIA, reinstalar drivers:
# 1. Download NVIDIA Driver 550+
# 2. Clean install (desabilitar Old driver)
# 3. Reiniciar
```

### Erro: CUDA not available

```powershell
# 1. Verificar driver
nvidia-smi

# 2. Reinstalar PyTorch para CUDA 12.1
poetry run pip uninstall -y torch
poetry run pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 3. Validar
poetry run python -c "import torch; print(torch.cuda.is_available())"
```

### Erro: Phi-3 não carrega (OutOfMemory)

RTX 3080 tem 10GB. Verificar:

```powershell
# 1. Verificar VRAM disponível
poetry run python -c "import torch; print(torch.cuda.get_device_properties(0))"

# 2. Se falhar, usar Qwen em vez de Phi
# 3. Ou usar quantização FP8:
#    pip install bitsandbytes
#    use_4bit: true (no YAML)
```

### Erro: torch installation fails

```powershell
# Limpar cache
poetry cache clear --all

# Reinstalar explicito
poetry run pip install --force-reinstall torch==2.0.0 --index-url https://download.pytorch.org/whl/cu121
```

### GPU muito quente (>85°C)

```powershell
# Monitorar temperatura
# Task Manager → Performance → GPU

# Se muito quente:
# 1. Verificar ventilação
# 2. Reduzir batch size
# 3. Usar FP32 em vez de FP16 (mais lento mas menos heat)
#    precision: fp32 (no YAML)
```

---

## 📈 Monitoramento

### Task Manager (Windows)

Performance → GPU → exibe:
- GPU utilização
- Memória
- Temperatura
- Power consump

### Logs da aplicação

```powershell
# Poetry
poetry run ar-api 2>&1 | Tee-Object -FilePath app.log

# Docker
docker logs -f ar-diagnostic-mvp
```

### gpumon (opcional)

```powershell
pip install gpumon
gpumon --interval 1
# Exibe GPU stats em tempo real
```

---

## 🔄 Atualizações

```powershell
cd backend_tcc_mvp

# Atualizar código
git pull origin main

# Reinstalar dependências
poetry install

# Se usar Docker
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔒 Segurança (Rede)

### Windows Firewall

```powershell
# Permitir porta 8000 (local only)
New-NetFirewallRule -DisplayName "AR-API" `
  -Direction Inbound -Action Allow `
  -Protocol TCP -LocalPort 8000 `
  -RemoteAddress 192.168.0.0/16
```

### HTTPS com nginx (opcional)

```powershell
# Instalar nginx via WSL2 ou standalone
# Configurar SSL certificate
# Usar nginx como reverse proxy para API
```

---

## 📚 Referências

- [NVIDIA Drivers](https://www.nvidia.com/Download/driverDetails.aspx)
- [CUDA 12.1 Toolkit](https://developer.nvidia.com/cuda-12-1-0-download-archive)
- [PyTorch Windows Install](https://pytorch.org/get-started/locally/)
- [Phi-3-mini - Hugging Face](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct)
- [Qwen2.5 - Hugging Face](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)
- [Docker Desktop Windows](https://docs.docker.com/desktop/install/windows-install/)

---

## ❓ FAQ

**P: Qual modelo para Legion?**  
A: **Phi-3-mini** (recomendado). Excelente qualidade, rápido (~300ms), cabe confortável em 10GB.

**P: Posso rodar em CPU só?**  
A: Sim, mas ~10x mais lento. Configure `device: cpu` no YAML.

**P: Quanto de VRAM preciso?**  
A: Mínimo 6GB (DialoGPT). 8GB confortável (Qwen). 10GB+ para Phi-3.

**P: RTX 3080 vs RTX 4090?**  
A: RTX 4090 (~50% mais rápido). Mas RTX 3080 é mais que suficiente para este projeto.

**P: Posso usar GPU integrada (iGPU)?**  
A: Não. iGPU é compartilhada com RAM (muito lento). Precisa de GPU dedicada.

**P: Quantos concurrent requests a API suporta?**  
A: ~5-10 com batch processing. PyTorch não é muito thread-safe, use fila.

**P: Posso servir a API na internet?**  
A: Sim, com HTTPS + auth. Configurar nginx reverse proxy ou usar ngrok para testing.
