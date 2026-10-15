# Platform Setup Guide

This guide explains how to run the AR Diagnostic MVP backend on each supported platform.

The project supports multiple deployment environments because each platform has different constraints regarding Python version, CUDA support, PyTorch wheels, model compatibility, and quantization.

---

## Quick Reference

| Platform | Script | Recommended Models | Notes |
|---|---|---|---|
| Desktop NVIDIA GPU | `setup_desktop_gpu.sh` / `setup_legion.ps1` | Qwen, Phi, DialoGPT | Ubuntu / Windows; supports NVIDIA GPUs such as RTX 5060 |
| Jetson AGX Orin | `setup_jetson_orin.sh` | Qwen, Phi, DialoGPT | Embedded high-performance target |
| Jetson Nano — native (JetPack 4.6) | `setup_poetry_nano.sh` | DialoGPT-small | Python 3.6.9 / CUDA 10.2 legacy stack |
| Jetson Nano — Ubuntu 20.04 | Manual system setup | Qwen | Community image; used for Qwen GPU experiments |

### Recommended Model by Platform

| Platform | Recommended | Alternatives |
|---|---|---|
| Desktop NVIDIA GPU | Qwen2.5-0.5B-Instruct | Phi-3 Mini, DialoGPT-small |
| Jetson AGX Orin | Qwen2.5-0.5B-Instruct | Phi-3 Mini, DialoGPT-small |
| Jetson Nano - native | DialoGPT-small | None recommended |
| Jetson Nano - Ubuntu 20.04 | Qwen2.5-0.5B-Instruct | DialoGPT-small |

Qwen provides the best latency/quality trade-off for the MVP. Phi-3 Mini provides better language quality at higher computational cost. DialoGPT-small is the ultra-lightweight baseline for constrained environments.

See [MODEL_SELECTION.md](MODEL_SELECTION.md) for a detailed comparison.

---

## 1. Desktop NVIDIA GPU

Use for development, debugging, benchmarking, and running modern CUDA-compatible models.

**Requirements:** Ubuntu or Windows x86_64, Python 3.10+, Poetry, and an NVIDIA driver with `nvidia-smi` working. The desktop profile installs the official PyTorch CUDA 12.8 wheel, so a system-wide CUDA Toolkit is not required.

### Setup

On Ubuntu:

```bash
bash setup_desktop_gpu.sh
```

The script detects any NVIDIA GPU through `nvidia-smi`, activates `pyproject-legion.toml`, rebuilds the lock file, installs dependencies, and verifies that PyTorch can use CUDA. The GPU model does not need to be named in the configuration.

On Windows PowerShell:

```powershell
.\setup_legion.ps1
```

If blocked by execution policy, run first:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

The script copies `pyproject-legion.toml`, rebuilds the lock file, installs dependencies, and verifies CUDA.

Manual setup:

```bash
cp pyproject-legion.toml pyproject.toml
poetry lock
poetry install
poetry run ar-api
```

---

## 2. Jetson AGX Orin

Use for embedded GPU deployment with a modern Jetson stack.

**Requirements:** JetPack 6.x, Python 3.10+, Poetry, CUDA available through the Jetson runtime, access to the Jetson AI Lab package index

### Setup

```bash
bash setup_jetson_orin.sh
```

The script copies `pyproject-jetson-orin.toml`, rebuilds the lock file, installs dependencies, verifies torch and accelerate versions against the Jetson AI Lab wheel index, and checks CUDA availability.

> **Note:** Automatic dependency resolution via Poetry can produce conflicts on Jetson platforms. The setup script applies a manually sequenced installation to ensure compatibility between PyTorch, CUDA, and the transformer libraries; the same strategy validated during the Orin experiments.

Manual setup:

```bash
cp pyproject-jetson-orin.toml pyproject.toml
poetry lock
poetry install
poetry run ar-api
```

---

## 3. Jetson Nano - Native (JetPack 4.6)

Use for DialoGPT-small execution on the official NVIDIA JetPack stack.

This is the recommended native configuration for the Jetson Nano. It runs on the official NVIDIA environment and achieves 0.363 s mean SLM latency and 2.76 diagnoses/s throughput with DialoGPT-small, comfortably meeting the 1.0 s target.

**Platform constraints:**

- JetPack 4.6.x / L4T R32.7.x
- CUDA 10.2
- Python 3.6.9
- PyTorch 1.10.0 NVIDIA wheel

> Qwen and Phi-3 are not supported in this environment. They require a newer Python and Transformers stack than the native Nano can support. Phi-3 Mini also exceeds the 4 GB VRAM budget.

### Background

Early Nano experiments with Qwen tried to force Python 3.8 on the JetPack 4.6 environment, but this created compatibility issues with the native CUDA/PyTorch stack and led to CPU fallback. As a result, latency increased significantly.

Switching back to the official NVIDIA JetPack stack with a manually sequenced installation resolved GPU execution for DialoGPT-small. For Qwen, the practical path was to use a separate Ubuntu 20.04 community image, where the newer userspace supported Qwen's dependency chain while still preserving CUDA access.

### Setup

```bash
export OPENBLAS_CORETYPE=ARMV8
bash setup_poetry_nano.sh
```

The `OPENBLAS_CORETYPE=ARMV8` export is required. Without it, numpy, cv2, and torch may fail with `Illegal instruction` on ARM.

To persist it:

```bash
echo 'export OPENBLAS_CORETYPE=ARMV8' >> ~/.bashrc
source ~/.bashrc
```

The script installs Poetry if needed, copies `pyproject-jetson-nano.toml`, installs dependencies, and installs torch 1.10.0 from the NVIDIA wheel.

---

## 4. Jetson Nano - Ubuntu 20.04 (Qwen Experiments)

Running Qwen2.5-0.5B on the Jetson Nano required a non-standard setup. A community-maintained Ubuntu 20.04 image was installed directly on a second Nano unit, providing a sufficiently modern userspace to support Qwen's dependency chain while retaining GPU access via CUDA.

This is not the recommended production path. It is documented here for reproducibility of the Qwen benchmark results reported in the thesis.

**Key result:** this configuration reduces Qwen latency from 15.388 s on CPU to 2.911 s on GPU, a 5.3× speedup, confirming that GPU activation is critical on constrained hardware and that Qwen is a viable but higher-latency alternative on the Nano.

> Phi-3 Mini could not be loaded on the Nano under any configuration; its memory requirements exceed the 4 GB VRAM budget.

### Setup Overview

Install the community Ubuntu 20.04 image on the Nano unit, then install system-level dependencies manually to ensure correct alignment between PyTorch, CUDA, and the transformer libraries. Automatic dependency resolution via Poetry is not reliable in this environment; packages must be installed in the correct order.

### Validation

```bash
python3 -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
# Expected: True
# Verify GPU is active before running benchmarks.
```

> If `torch.cuda.is_available()` returns False, the pipeline will silently fall back to CPU. Latency will be approximately 5× higher and results will not match the reported benchmarks.

---

## Running the API

**Foreground:**

```bash
poetry run ar-api
```

or:

```bash
poetry run python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

---

## Troubleshooting

**Jetson Nano shows "Illegal instruction"**

Set `export OPENBLAS_CORETYPE=ARMV8`. This prevents OpenBLAS from selecting unsupported kernels on Jetson Nano ARM.

**Out of memory on Jetson Nano**

Monitor with `sudo tegrastats`. Optionally free memory by stopping the graphical interface:

```bash
sudo systemctl stop lightdm
```

**Model loading fails**

Check the selected YAML configuration: `models.default`, local model path (when using cached models), CUDA availability, and whether the model is compatible with the selected platform.