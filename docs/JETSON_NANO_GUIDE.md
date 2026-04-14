# 📄 Jetson Nano Setup & Deployment Guide (Final Version)

## Overview

Guia completo para setup e execução do AR Diagnostic MVP no **Jetson Nano (4GB)** com **JetPack 4.6** (L4T R32.7).

⚠️ **Este guia reflete a stack validada experimentalmente (March 2026).**
Inclui limitações reais da plataforma e decisões de engenharia adotadas durante o desenvolvimento.

---

## 📌 Stack Validada (Produção)

| Componente | Versão | Status | Nota |
|---|---|---|---|
| **Jetson Nano** | Tegra X1 4GB | ✅ Testado | Memória compartilhada GPU/CPU |
| **JetPack** | 4.6.x | ✅ Estável | Base oficial NVIDIA |
| **L4T** | R32.7.x | ✅ Estável | Kernel validado |
| **Python** | 3.6.9 | ✅ Estável | Limitação de stack legado |
| **PyTorch** | 1.10.0 | ✅ Estável | Stack validada com CUDA 10.2 |
| **CUDA** | 10.2 | ✅ Estável | Compatível com Maxwell (compute 5.3) |
| **Transformers** | 4.8.2 | ✅ Estável | Última versão compatível com PyTorch 1.10 |
| **Modelo** | DialoGPT-small | ✅ Compatível | 117M params, ~250 MB VRAM |

---

## 🎯 Recommended Setup

**Use the validated setup script:**

```bash
cd ~/backend_tcc_mvp
bash setup_poetry_nano.sh

# Required optimization for ARM
export OPENBLAS_CORETYPE=ARMV8

poetry run ar-api
```

**What the script does:**
- Installs Poetry
- Configures environment for Jetson Nano
- Installs compatible dependencies
- Validates PyTorch + CUDA
- Prepares the runtime environment

---

## 📋 Prerequisites

**Check JetPack / L4T**
```bash
cat /etc/nv_tegra_release
# Expected: R32.7.x
```

**Check Python**
```bash
python3 --version
# Expected: 3.6.9
```

---

## 🚀 Manual Setup (Fallback)

If the script fails:

```bash
cd ~/backend_tcc_mvp

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"

# Activate Jetson config
cp pyproject-jetson-nano.toml pyproject.toml

# Install dependencies
poetry env use python3
poetry install --no-dev

# Critical optimization
export OPENBLAS_CORETYPE=ARMV8

# Run API
poetry run ar-api
```

**Persist environment:**

```bash
echo 'export OPENBLAS_CORETYPE=ARMV8' >> ~/.bashrc
source ~/.bashrc
```

---

## ⚙️ Configuration (YAML)

Optimized configuration for Jetson Nano:

```yaml
models:
  default: dialogpt-small
  device: cuda
  use_4bit: false
  greedy_decoding: true
  prompt_max_length: 256
  warmup_on_startup: true

dialogpt-small:
  name: /home/das9/models/DialoGPT-small  # adjust for your environment
  max_tokens: 40
  summary_tokens: 60
  temperature: 0.3
  top_p: 0.85
```

⚠️ **Adjust model path according to your local setup.**

---

## 🧪 Validation

**CUDA Check**
```bash
python3 -c "import torch; print(torch.cuda.is_available())"
# Expected: True
```

**API Health**
```bash
curl http://localhost:8000/health
```

**Test Request**
```bash
curl -X POST http://localhost:8000/diagnose \
  -F "file=@image.jpg" \
  -F "frame_index=0"
```

---

## 📊 Performance (Measured)

| Metric | Value |
|---|---|
| PDI (per frame) | ~90 ms |
| LLM inference | ~250 ms |
| Batch (10 frames) | ~3.4 s |
| VRAM usage | ~2.2 GB |
| Throughput | ~3 FPS |

---

## 🛠️ Troubleshooting

**CUDA not available**
```bash
python3 -c "import torch; print(torch.cuda.is_available())"
```
If False, verify JetPack installation.

**Out of Memory**
```bash
sudo tegrastats
sudo systemctl stop lightdm
```

**Torch not found**
```bash
python3 -c "import torch; print(torch.__version__)"
```

Reinstall if needed:

```bash
pip install https://nvidia.box.com/shared/static/p57jwntjetr23c7d647vsd20tkgp4b3a.whl
```

---

## � Monitoring

```bash
sudo tegrastats
```

Displays:

- CPU
- GPU
- RAM
- Temperature

---

## ⚠️ Known Limitations

### Model Constraints

Only DialoGPT-small is supported in this stack. Larger models exceed memory or compatibility limits.

### Unsupported Approaches

| Approach | Reason |
|---|---|
| Qwen 0.5B | Requires newer Transformers / Python |
| Phi-3 Mini | Exceeds memory (~7GB) |
| 4-bit quantization | Unsupported on Maxwell GPU |
| bitsandbytes | Requires compute ≥ 7.5 |

---

## ❓ FAQ

**Can I run Qwen on Jetson Nano?**

No. Besides memory constraints, it requires a newer software stack incompatible with JetPack 4.6.

**Can I use quantization?**

No. Maxwell GPUs (compute 5.3) do not support modern quantization libraries.

**Why DialoGPT?**

It provides the best trade-off between:

- Latency
- Memory usage
- Compatibility

---

## 📚 References

- [NVIDIA Jetson Nano Docs](https://docs.nvidia.com/jetson/jetson-nano/index.html)
- [Hugging Face Transformers](https://huggingface.co/transformers/)
- [PyTorch for Jetson (NVIDIA forums)](https://forums.developer.nvidia.com/)
