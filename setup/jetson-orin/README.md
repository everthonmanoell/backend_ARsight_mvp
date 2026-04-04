# Setup Jetson Orin — AR Diagnostic MVP

Guia completo para configurar o ambiente no Jetson Orin (JetPack 6.x).

## ✅ Pré-requisitos

Antes de executar o setup, verifique:

```bash
# JetPack 6.0+
cat /etc/nv_tegra_release | grep "R36"
# Esperado: R36.x

# CUDA 12.6+
nvidia-smi
# Esperado: CUDA 12.6 ou superior

# Python 3.10+
python3 --version
# Esperado: Python 3.10+

# Poetry
poetry --version
# Se não tiver: pip install poetry
```

---

## 🚀 Setup Automático

Execute o script de setup (a partir da raiz do projeto):

```bash
cd ~/backend_tcc_mvp
bash setup/jetson-orin/setup.sh
```

**O que o script faz:**

1. ✅ Verifica versões de pytorch e accelerate instaladas
2. ✅ Instala dependências Poetry (`poetry install`)
3. ✅ Instala PyTorch 2.8.0 com CUDA 12.6 do Jetson AI Lab
4. ✅ Instala Accelerate 1.2.1 (otimizado para Jetson)
5. ✅ Valida disponibilidade de CUDA e GPU

**Tempo esperado:** 10-15 minutos (dependendo da conexão e velocidade do Jetson)

---

## 🔍 Verificação Manual (alternativa)

Se preferir fazer passo a passo:

### Passo 1: Instalar dependências Poetry
```bash
poetry install
```

### Passo 2: Instalar PyTorch com CUDA 12.6
```bash
poetry run pip install torch==2.8.0 --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
```

### Passo 3: Instalar Accelerate (otimizado)
```bash
poetry run pip install --no-deps accelerate==1.2.1
```

### Passo 4: Validar instalação
```bash
poetry run python3 -c "
import torch
import accelerate
print(f'✓ torch: {torch.__version__}')
print(f'✓ accelerate: {accelerate.__version__}')
print(f'✓ CUDA: {torch.cuda.is_available()}')
print(f'✓ Device: {torch.cuda.get_device_name(0)}')
"
```

---

## 🎯 Executar o Projeto

### API REST
```bash
poetry run ar-api
```

Acesse: `http://localhost:8000/docs` (Swagger UI)

### Pipeline de Teste (True Batch)
```bash
poetry run python tests/manual/test_pipeline.py
```

### Testes Unitários
```bash
poetry run pytest tests/
```

---

## ⚙️ Configuração de Precisão

O sistema usa **FP16 automaticamente** no Jetson Orin para otimizar memória (32GB compartilhada).

```bash
# FP16 automático (padrão - recomendado)
poetry run ar-api

# FP32 fallback (se houver problemas)
MODEL_PRECISION=fp32 poetry run ar-api
```

Verifique qual está sendo usado:
```bash
poetry run python -c "
from app.config.config import Config
config = Config()
print(f'Precision: {config.get(\"models.precision\", \"auto\")}')
"
```

---

## 📊 Monitorar GPU

Durante execução, em outro terminal:

```bash
# Monitorar uso de VRAM (memória unificada)
watch -n 1 nvidia-smi

# Ou com tegrastats (mais detalhado)
sudo tegrastats
```

Esperado: GPU utilizando 30-60% de VRAM durante pipeline.

---

## 🐛 Troubleshooting

### CUDA não está disponível

```bash
# Verificar drivers
nvidia-smi  # deve funcionar

# Reconstruir pyproject.lock
poetry cache clear --all
poetry lock --no-cache --regenerate
poetry install

# Reinstalar torch especificamente
poetry run pip install --force-reinstall torch==2.8.0 --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
```

### PyTorch build do Jetson não encontrado

À vezes o índice `pypi.jetson-ai-lab.io` fica indisponível. Tente:

```bash
# Alternativas (com CUDA 12.1+)
poetry run pip install torch==2.8.0+cu121  # Pode não funcionar bem com CUDA 12.6

# Ou baixar wheel manualmente
# Consulte https://pypi.jetson-ai-lab.io/jp6/cu126/
```

### Memory Exhausted durante inferência

Jetson Orin tem 32GB compartilhada. Se receber Out of Memory:

1. Reduza `batch_size` em `app/config/thresholds.yaml`
2. Use FP32 em vez de FP16: `MODEL_PRECISION=fp32 poetry run ar-api`
3. Feche outras aplicações

### Modelo não carrega

```bash
# Verifique download de modelo
poetry run python -c "
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-0.5B-Instruct')
print('✓ Modelo carregado')
"

# Se falhar:
huggingface-cli login  # Faça login no Hugging Face
poetry run python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-0.5B-Instruct')"
```

---

## 📈 Performance Esperada

| Métrica | Esperado |
|---------|----------|
| Latência (Qwen 0.5B) | ~1s |
| Latência (Phi-3 Mini) | ~1.5s |
| Throughput (batch 10) | ~10-12s |
| GPU Usage | 40-60% VRAM |
| CPU Usage | 2-4 cores |

---

## 🔗 Links Úteis

- [JetPack 6.0 Docs](https://docs.nvidia.com/jetpack/archives/jetpack-6/)
- [Jetson AI Lab PyTorch](https://pypi.jetson-ai-lab.io/)
- [Hugging Face Models](https://huggingface.co/models)
- [Qwen 2.5 0.5B](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)
- [Phi-3 Mini](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct)

---

## ❓ FAQ

**P: Posso usar Jetson Nano?**
A: Não recomendado. Há limite extremo de VRAM (2GB) e não suporta CUDA 12.6. Use Jetson Orin ou desktop.

**P: Qual é a diferença entre Orin NX e AGX Orin?**
A: AGX Orin é mais potente (12 cores GPU), mas setup é idêntico. Orin NX tem menos cores (8), mas todas as outras especificações são iguais.

**P: Posso voltar para Jetson com Jetson Nano depois?**
A: `pyproject.toml` é versionada. Outros ambientes têm alias:
- Jetson Orin: `pyproject.toml`
- Desktop Legion: `pyproject-legion.toml`

**P: Como atualizar modelos LLM?**
A: Editar `app/config/config.py`:
```yaml
models:
  default: qwen  # mude para phi, llama, etc
  qwen:
    version: Qwen/Qwen2.5-0.5B-Instruct
```

---

## 📞 Suporte

Se tiver problemas:

1. Consulte [setup/TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
2. Verifique logs: `poetry run python tests/manual/test_pipeline.py 2>&1 | head -50`
3. Check [SETUP_INSTRUCTIONS.md](../../SETUP_INSTRUCTIONS.md) para ambiente completo
