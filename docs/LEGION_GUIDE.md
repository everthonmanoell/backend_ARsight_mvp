# Desktop Legion Setup & Deployment Guide

## Overview

Guia completo para setup e execução do AR Diagnostic MVP no desktop Legion com GPU NVIDIA.

⚠️ **Este guia reflete a stack validada experimentalmente no projeto.**  
O foco principal é o uso de setup local com Poetry, com suporte aos modelos utilizados nos benchmarks principais do sistema.

## Recommended Models on Legion

- **Qwen2.5-0.5B**: melhor trade-off entre latência e qualidade
- **Phi-3-mini**: melhor qualidade textual, com maior custo de inferência

Ver [MODEL_SELECTION.md](MODEL_SELECTION.md) para comparação detalhada.

## Validated Scope

Este guia se refere ao ambiente desktop Legion utilizado nos experimentos do projeto.

| Component | Version / Family | Status | Notes |
|---|---|---|---|
| **Desktop Legion** | x86_64 workstation / laptop | ✅ Validated | Main desktop benchmark platform |
| **OS** | Ubuntu 22.04 | ✅ Stable | Validated in project environment |
| **Python** | 3.10+ | ✅ Stable | Compatible with modern ML stack |
| **PyTorch** | 2.x | ✅ Stable | CUDA-enabled |
| **CUDA** | 12.x | ✅ Stable | Desktop NVIDIA stack |
| **Transformers** | 4.4x+ | ✅ Compatible | Supports recent architectures |
| **Qwen2.5-0.5B** | Supported | ✅ Recommended | Best latency/quality trade-off |
| **Phi-3-mini** | Supported | ✅ Optional | Better quality, higher latency |

## Main Recommendation

**Use the local Poetry-based setup.**

```bash
cd ~/backend_tcc_mvp

# Use the desktop Legion configuration
cp pyproject-legion.toml pyproject.toml

# Install dependencies
poetry install

# Run API
poetry run ar-api
```

**This is the recommended workflow for:**

- development
- testing
- benchmark execution
- model comparison

## Prerequisites

**Check Python**

```bash
python3 --version
# Expected: 3.10.x or newer
```

**Check CUDA availability**

```bash
python3 -c "import torch; print(torch.cuda.is_available())"
# Expected: True
```

**Check NVIDIA driver**

```bash
nvidia-smi
```

## Local Setup with Poetry

**Recommended**

```bash
cd ~/backend_tcc_mvp
cp pyproject-legion.toml pyproject.toml
poetry env use python3
poetry install
poetry run ar-api
```

**If Poetry is not installed**

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
poetry --version
```

**Persist path if needed**

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Configuration (YAML)

**Typical configuration for Qwen on Legion:**

```yaml
models:
  default: qwen
  device: cuda
  use_4bit: false
  greedy_decoding: false
  prompt_max_length: 512
  warmup_on_startup: true

  qwen:
    name: Qwen/Qwen2.5-0.5B-Instruct
    max_tokens: 100
    summary_tokens: 150
    temperature: 0.3
    top_p: 0.85

  phi:
    name: microsoft/Phi-3-mini-4k-instruct
    max_tokens: 120
    summary_tokens: 200
    temperature: 0.3
    top_p: 0.85
```

**Suggested usage**

- Qwen → recommended for production and benchmarks
- Phi-3-mini → recommended when explanation quality is prioritized over latency

## Validation

**CUDA status**

```bash
python3 -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'Device: {torch.cuda.get_device_name(0)}')
    print(f'Capability: {torch.cuda.get_device_capability(0)}')
"
```

**API health**

```bash
curl http://localhost:8000/health
```

**Test request**

```bash
curl -X POST http://localhost:8000/diagnose \
  -F "file=@image.jpg" \
  -F "frame_index=0"
```

## Performance Expectations

**Performance depends on:**

- selected model
- batch size
- prompt length
- warmup state
- CUDA / PyTorch tuning

**Observed behavior in the project**

| Model | Profile | Notes |
|---|---|---|
| DialoGPT-small | Fastest baseline | Lowest explanation quality |
| Qwen2.5-0.5B | Best trade-off | Recommended option |
| Phi-3-mini | Highest quality | Slower than Qwen |

**Typical batch behavior**

For batch processing with 10 frames:

- Qwen: best overall trade-off on Legion
- Phi-3-mini: feasible, with higher latency
- DialoGPT-small: useful as lightweight baseline

**Exact latency should be reported from the benchmark outputs generated in this repository.**

## Troubleshooting

**CUDA not available**

```bash
python3 -c "import torch; print(torch.cuda.is_available())"
```

If False:

- verify NVIDIA driver installation
- verify CUDA-enabled PyTorch
- verify environment setup

**CPU-only PyTorch installed**

```bash
python3 -c "import torch; print(torch.__version__)"
```

If the version indicates CPU-only build, reinstall the CUDA-enabled package used in the validated setup.

**Model loading fails**

Check:

- model path
- transformers version
- available GPU memory
- YAML configuration

**High VRAM usage**

```bash
nvidia-smi
```

If memory becomes too high:

- close other GPU-intensive applications
- reduce concurrent processes
- reduce batch size for debugging

## Monitoring

**Use:**

```bash
nvidia-smi
```

This is the recommended monitoring tool on the Legion desktop. It provides:

- GPU memory usage
- GPU utilization
- driver and CUDA information
- running GPU processes

## Docker Status

⚠️ **Docker is not the recommended path for the Legion setup in this project.**

The validated workflow is the local Poetry-based environment.

Docker may still be used experimentally, but it is not the primary execution path documented here.

## Known Trade-offs

**Qwen vs Phi**

| Model | Advantage | Drawback |
|---|---|---|
| Qwen2.5-0.5B | Better latency | Slightly lower explanation quality |
| Phi-3-mini | Better explanation quality | Higher latency |

**Legion vs Orin**

The Legion may outperform Jetson Orin in practice depending on:

- x86 vs ARM software maturity
- NVIDIA desktop driver stack
- CUDA / PyTorch optimization
- model loading behavior

## FAQ

**Which model should I use on Legion?**

Use Qwen2.5-0.5B as the default choice. It offers the best balance between throughput and explanation quality.

**Can I use Phi-3-mini on Legion?**

Yes. It is feasible and useful when explanation quality is more important than latency.

**Is 4-bit quantization required?**

No. The Legion can run the validated models without requiring 4-bit quantization. FP16 is often the safer default.

**Is Legion faster than Orin?**

Often yes, depending on the software stack and optimization level.

**Should I use Docker on Legion?**

Not as the main workflow for this project. Prefer the local Poetry-based setup.

## References

- [PyTorch](https://pytorch.org/)
- [Hugging Face Transformers](https://huggingface.co/transformers/)
- [Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)
- [Phi-3-mini-4k-instruct](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct)
