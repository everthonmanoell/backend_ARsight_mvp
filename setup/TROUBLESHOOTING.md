# Troubleshooting — Setup e Instalação

Soluções para problemas comuns de setup em ambos os ambientes.

---

## 🪟 Windows

### CUDA não encontrado

**Sintoma:** `torch.cuda.is_available()` retorna `False`

```powershell
# Verficar drivers
nvidia-smi

# Se funciona mas torch ainda não vê CUDA:
poetry run pip install --force-reinstall torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Se nvidia-smi não funciona:
# 1. Instale drivers: https://www.nvidia.com/Download/
# 2. Reinicie Windows
# 3. Teste nvidia-smi novamente
```

### Script não executa

**Sintoma:** `cannot be loaded because running scripts is disabled`

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup\legion-windows\setup.ps1
```

### Poetry lock/install falha

```powershell
# Limpar tudo e começar do zero
poetry cache clear --all
Remove-Item poetry.lock -Force
Remove-Item ".venv" -Recurse -Force -ErrorAction SilentlyContinue
poetry lock --no-cache --regenerate
poetry install
```

### Erro `SyntaxError` ao rodar tests

**Solução:** Verificar versão de Python
```powershell
python --version  # Deve ser 3.10+

# Se tiver 3.12 ou mais novo, pode haver incompatibilidade
# Use Python 3.10 ou 3.11
```

---

## 🐧 Linux (Jetson Orin)

### CUDA não disponível

**Sintoma:** `torch.cuda.is_available()` retorna `False`

```bash
# Verificar:
nvidia-smi
cat /etc/nv_tegra_release | grep "R36"  # Deve ser R36.x

# Se CUDA não funciona:
poetry cache clear --all
poetry lock --no-cache --regenerate
poetry install

# Reinstalar torch do Jetson AI Lab:
poetry run pip install --force-reinstall torch==2.8.0 \
  --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
```

### Jetson AI Lab index indisponível

**Sintoma:** `ERROR: Could not find a version that satisfies the requirement torch==2.8.0`

```bash
# Tente alternativa com CUDA 12.1 (menos otimizada):
poetry run pip install torch==2.8.0+cu121

# Ou aguarde https://pypi.jetson-ai-lab.io/ voltar online
```

### Out of Memory

**Sintoma:** `RuntimeError: CUDA out of memory`

```bash
# Monitorar uso
sudo tegrastats

# Soluções:
# 1. Reduza batch size em app/config/thresholds.yaml
# 2. Use FP32:
MODEL_PRECISION=fp32 poetry run ar-api

# 3. Feche outras aplicações
pkill -f "python"  # Cuidado: mata todos os Python
```

### Modelo não carrega

```bash
poetry run python -c "
from transformers import AutoModelForCausalLM
AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-0.5B-Instruct')
print('✓ OK')
"

# Se falhar, tente:
huggingface-cli login
```

---

## 🔄 Ambos (Windows + Jetson)

### Import error: módulo não encontrado

```bash
# Poetry não está usando o ambiente correto
poetry run python --version  # Verifique versão
poetry install --no-cache    # Reinstale

# Se persistir:
poetry cache clear --all
poetry env info
```

### Poetry.lock corrompido

```bash
# Deletar e reconstruir
rm -f poetry.lock              # Linux/Jetson
Remove-Item poetry.lock -Force # Windows

poetry lock --no-cache --regenerate
poetry install
```

### Erro ao baixar modelos do Hugging Face

**Sintoma:** `Connection error` ou timeout

```bash
# Tente manualmente em outro terminal
huggingface-cli download Qwen/Qwen2.5-0.5B-Instruct

# Se falhar, verifique proxy/firewall
# Ou use cache:
HF_DATASETS_CACHE=/path/to/cache poetry run python ...
```

---

## 🔨 Verificação Completa

Execute este script de diagnóstico:

```bash
# Linux/Jetson
poetry run python << 'EOF'
import platform
import torch
import transformers
import accelerate
import sys

print("=== VERIFICAÇÃO ===")
print(f"Python: {sys.version}")
print(f"Platform: {platform.machine()}")
print(f"PyTorch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
print(f"Transformers: {transformers.__version__}")
print(f"Accelerate: {accelerate.__version__}")
EOF
```

```powershell
# Windows
poetry run python -c "
import platform, torch, transformers, accelerate, sys
print(f'Python: {sys.version}')
print(f'Platform: {platform.machine()}')
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'Device: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB')
print(f'Transformers: {transformers.__version__}')
print(f'Accelerate: {accelerate.__version__}')
"
```

---

## 🆘 Ainda não resolveu?

1. **Verificar logs detalhados:**
```bash
# Com verbose
poetry run python -c "import torch; print(torch.__version__)" -v  # Não existe, mas:
PYTORCH_CUDA_ALLOC_CONF=:16 poetry run python tests/manual/test_pipeline.py 2>&1 | head -50
```

2. **Consultar documentação oficial:**
   - [PyTorch CUDA Setup](https://pytorch.org/get-started/locally/)
   - [Transformers Installation](https://huggingface.co/docs/transformers/installation)
   - [Jetson AI Lab](https://pypi.jetson-ai-lab.io/)

3. **Criar fresh venv:**
```bash
# Linux/Jetson
poetry env remove python3
poetry env use python3.10
poetry install

# Windows
poetry cache clear --all
poetry install --no-cache
```

---

## 📝 Comandos Rápidos de Referência

### Diagnosticar ambiente
```bash
poetry run python -c "from app.config.config import Config; c=Config(); print(c.config)"
```

### Testar GPU
```bash
poetry run python -c "
import torch
x = torch.randn(1000, 1000).cuda()
y = torch.randn(1000, 1000).cuda()
z = torch.matmul(x, y)
print(f'✓ GPU OK: {z.shape}')
"
```

### Forçar recriação de ambiente
```bash
# Linux/Jetson
rm -rf .venv poetry.lock
poetry install

# Windows
Remove-Item .venv -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item poetry.lock -Force
poetry install
```

---

## 🔗 Referências

- [CUDA Capability Checker](https://developer.nvidia.com/cuda-gpus)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [Transformers Docs](https://huggingface.co/docs/transformers/)
- [Jetson Docs](https://docs.nvidia.com/jetpack/)
