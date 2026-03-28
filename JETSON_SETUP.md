# Jetson AGX Orin Setup (PyTorch + CUDA)

## Problema Principal

O `pyproject.toml` não deve mencionar `torch` diretamente, pois o Poetry tentaria resolver uma versão do PyPI, que para aarch64 é CPU-only. Isso causava reverter para `torch 2.7.1+cpu`, perder CUDA e travar o modelo.

## Solução: Separação entre Poetry e Pip

1. **Poetry** gerencia: FastAPI, transformers, accelerate, opencv-python-headless, etc.
2. **Pip** (manual) provê: `torch==2.8.0` compilado com CUDA 12.6 da Jetson AI Lab

Isso evita conflitos de resolução.

---

## Quick Start (Jetson AGX Orin)

### 1. Clone o repositório
```bash
git clone <seu-repo>
cd backend_tcc_mvp
```

### 2. Instale via Poetry
```bash
poetry install
```

### 3. Instale torch com CUDA (obrigatório)
```bash
poetry run pip install torch==2.8.0 --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
```

**Se precisar corrigir uma instalação quebrada:**
```bash
poetry run pip install --no-cache-dir --force-reinstall torch==2.8.0 --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
```

### 4. Valide a instalação
```bash
poetry run python -c "import torch; print('torch:', torch.__version__); print('cuda:', torch.cuda.is_available()); print('cuda version:', torch.version.cuda); print('devices:', torch.cuda.device_count())"
```

**Esperado:**
```
torch: 2.8.0
cuda: True
cuda version: 12.6
devices: 1
```

---

## Running the API

### Default (production mode - CUDA funciona corretamente)
```bash
poetry run ar-api
```

### Development mode (com auto-reload - cuidado: CUDA pode não detectar corretamente em subprocessos)
```bash
poetry run uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Documentação interativa
```
http://localhost:8000/docs
```

---

## FP16 Automático

A aplicação detecta:
- **Jetson** (aarch64) → FP16 (torch.float16)
- **Desktop** (x86_64) → FP32 (torch.float32)

Para forçar FP32 em Jetson:
```bash
MODEL_PRECISION=fp32 poetry run ar-api
```

---

## Troubleshooting

### "CUDA returned an error code"
Reinstale torch (Python/Poetry environment corrompido):
```bash
poetry run pip install --force-reinstall torch==2.8.0 --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
```

Se o erro persistir, limpe completamente:
```bash
poetry run pip uninstall -y torch
poetry run pip install torch==2.8.0 --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
```

### "torch.cuda.is_available() = False"
**Causa:** Modo reload do Uvicorn (workers perdem contexto CUDA)
**Solução:** Use `--no-reload`:
```bash
poetry run uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --no-reload
```

### "ModuleNotFoundError: No module named 'torch'"
Python não encontra torch (não foi instalado):
```bash
poetry run pip install torch==2.8.0 --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
```

Se erro persistir, refaça tudo:
```bash
poetry install
poetry run pip install torch==2.8.0 --index-url https://pypi.jetson-ai-lab.io/jp6/cu126
poetry run python -c "import torch; print('✅ torch OK:', torch.__version__)"
```

---

## pyproject.toml - O que NÃO deve estar lá

❌ **NÃO incluir:**
```toml
torch = ">=2.0.1,<3.0"
torchvision = "..."
torchaudio = "..."
bitsandbytes = "..."
```

✅ **DEVE incluir:**
```toml
numpy = ">=1.26.0,<2.0"
opencv-python-headless = "4.10.0.84"  # Não opencv-python
accelerate = "^1.2.1"  # Este OK, pois não é torch (usa o torch já instalado)
```

---

## Hardware Target

- **Device:** Jetson AGX Orin
- **VRAM:** 32GB unificada
- **JetPack:** 6.x (L4T R36.4.4)
- **CUDA Driver:** 12060 (suporta até CUDA 12.6)
- **PyTorch:** 2.8.0 (cu126)
- **Python:** 3.10

---

## References

- **Jetson AI Lab PyPI:** https://pypi.jetson-ai-lab.io/
- **JetPack Docs:** https://developer.nvidia.com/jetpack
- **PyTorch for Jetson:** https://pytorch.org/
