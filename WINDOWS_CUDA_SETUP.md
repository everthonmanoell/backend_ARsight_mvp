# CUDA Setup no Windows — Guia Completo

Para usar CUDA no PC Legion com Windows, é necessário ter drivers NVIDIA e CUDA Toolkit instalados corretamente.

## ✅ Pré-requisitos

### 1. GPU NVIDIA Compatível
- RTX 20 series ou mais novo (RTX 3080, 4090, etc.)
- CUDA Capability 7.0+ (verify em [NVIDIA CUDA GPU](https://developer.nvidia.com/cuda-gpus))

### 2. Drivers NVIDIA (Versão 550+)

**Windows Usar GPU Driver**
1. Abra [NVIDIA Driver Download](https://www.nvidia.com/Download/driverDetails.aspx/)
2. Selecione sua GPU
3. Baixe versão 550+ para CUDA 12.1
4. Instale e **reinicie**

**Verificar instalação:**
```powershell
nvidia-smi
# Deve exibir GPU, driver version (550+), e CUDA capability
```

### 3. CUDA Toolkit 12.1 (Opcional)

Se CUDA não estiver disponível via drivers:

1. Download [NVIDIA CUDA Toolkit 12.1](https://developer.nvidia.com/cuda-12-1-0-download-archive)
2. Escolha: Windows → 11 → x86_64 → exe (local)
3. Instale (pode demorar alguns minutos)
4. Após instalar, **reinicie**

**Verificar após instalação:**
```powershell
nvidia-smi
```

### 4. Python 3.10+ e Poetry

```powershell
# Python
python --version  # deve ser 3.10+

# Poetry
poetry --version   # deve estar disponível

# Se não tiver Poetry:
pip install poetry
```

---

## 🚀 Setup Legacy (Este Projeto)

### Opção 1: Script Automático (Recomendado)

```powershell
cd backend_tcc_mvp
.\setup_legion.ps1
```

O script fará automaticamente:
- ✅ Ativar `pyproject-legion.toml`
- ✅ Instalar PyTorch com CUDA 12.1
- ✅ Validar CUDA disponível

### Opção 2: Manual

```powershell
cd backend_tcc_mvp

# 1. Ativar configuração
Move-Item pyproject.toml pyproject-jetson.toml -Force
Move-Item pyproject-legion.toml pyproject.toml -Force

# 2. Instalar
Remove-Item poetry.lock -Force -ErrorAction SilentlyContinue
poetry lock
poetry install

# 3. Validar CUDA
poetry run python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

---

## 🔍 Validação

### CUDA Status Completo

```powershell
poetry run python << 'EOF'
import torch
import accelerate
import transformers

print("=== PyTorch ===")
print(f"Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"CUDA Capability: {torch.cuda.get_device_capability(0)}")
else:
    print("❌ CUDA NÃO DISPONÍVEL")
    exit(1)

print("\n=== Dependencies ===")
print(f"Transformers: {transformers.__version__}")
print(f"Accelerate: {accelerate.__version__}")

print("\n✅ Tudo pronto para usar GPU")
EOF
```

### Teste Simples de GPU

```powershell
poetry run python << 'EOF'
import torch

# Criar tensor na GPU
x = torch.randn(1000, 1000).cuda()
y = torch.randn(1000, 1000).cuda()

# Multiplicação
z = torch.matmul(x, y)

print(f"✅ GPU operações funcionando!")
print(f"Resultado shape: {z.shape}")
EOF
```

---

## 🛠️ Troubleshooting

### Problema: `nvidia-smi` não encontrado

**Solução:**
1. Reinstale drivers NVIDIA (versão 550+)
2. Verifique PATH do sistema
3. Reinicie PowerShell após instalar drivers

```powershell
# Adicionar CUDA ao PATH (opcional)
$env:PATH += ";C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\bin"
```

### Problema: CUDA available mas erro ao usar

```powershell
# 1. Reinstale PyTorch
poetry run pip uninstall -y torch torchvision torchaudio
poetry run pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 2. Clear cache
poetry cache clear --all

# 3. Teste novamente
poetry run python -c "import torch; print(torch.cuda.is_available())"
```

### Problema: torch.cuda.OutOfMemory

**Para desenvolvimento:**
```powershell
# Reduz batch size ou use CPU
poetry run python -c "import torch; torch.cuda.empty_cache()"

# Monitorar GPU
# Abrir Task Manager → desempenho → GPU
```

### Problema: Runtime error ao carregar modelo

```powershell
# Tente FP32 em vez de FP16
MODEL_PRECISION=fp32 poetry run ar-api

# Ou para verificação rápida:
poetry run python << 'EOF'
import torch

# Teste loading simples
device = torch.device("cuda")
x = torch.zeros(1000, 1000, device=device, dtype=torch.float16)
y = torch.zeros(1000, 1000, device=device, dtype=torch.float32)

print("✅ FP16 e FP32 funcionam")
EOF
```

---

## 📊 Performance

### Validar GPU em uso

```powershell
# Enquanto roda poetry run ar-api
# Em outro terminal PowerShell:

while ($true) { nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader; Start-Sleep -Seconds 1 }
# Deve mostrar 40-80% durante processamento
```

---

## ❓ FAQ

**P: Qual é a diferença entre CUDA via drivers e CUDA Toolkit?**
A: Drivers NVIDIA já incluem CUDA runtime. CUDA Toolkit é para development (compilar kernels custom). Para este projeto, apenas drivers são necessários.

**P: Preciso de cuDNN?**
A: Não, PyTorch já vem com cuDNN otimizado.

**P: Quanto de VRAM é necessário?**
A: Mínimo 6GB (para Phi-3 Mini). RTX 3080+ (10GB+) é confortável.

**P: Posso rodar em CPU em vez de GPU?**
A: Sim, removing `.cuda()` no código, mas será ~10x mais lento.

---

## 🔗 Links Úteis

- [NVIDIA Drivers](https://www.nvidia.com/Download/driverDetails.aspx)
- [CUDA 12.1 Download](https://developer.nvidia.com/cuda-12-1-0-download-archive)
- [PyTorch Windows Install](https://pytorch.org/get-started/locally/)
- [CUDA Compute Capability](https://developer.nvidia.com/cuda-gpus)
