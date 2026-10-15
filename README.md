# ARSight Backend - MVP Version

![Python](https://img.shields.io/badge/Python-3.6%2B-3776AB?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)
![PyTorch](https://img.shields.io/badge/PyTorch-1.10%2B-EE4C2C?logo=pytorch)
![License](https://img.shields.io/badge/license-MIT-green)

**ARSight Backend MVP** is a FastAPI-based backend for illumination quality diagnosis in augmented reality scenes, designed to run on constrained embedded hardware without relying on cloud infrastructure.

The system combines deterministic luminance-based image analysis, rule-based classification, and Small Language Model inference to produce structured, human-readable AR readiness assessments. It was deployed and validated across three heterogeneous hardware platforms: a desktop workstation, a Jetson AGX Orin, and a Jetson Nano.

### Related Repositories

| Repository | Description |
|---|---|
| [ar_sight](https://github.com/daniamorimdesa/ar_sight) | Mobile Flutter frontend for AR scene capture and diagnosis visualization |
| [backend_tcc_ar_sight](https://github.com/daniamorimdesa/backend_tcc_ar_sight) | Full-scope exploratory backend with four planned diagnostic metrics |
| `backend_tcc_mvp` | This repository (final MVP focused on illumination diagnosis) |

---

## Project Context

This repository is the final MVP used in the TCC research and experimental validation. The scope was deliberately focused on illumination analysis, the most critical and mature descriptor for the embedded pipeline, while the broader set of metrics explored during the project (texture, occlusion, reflection) is preserved in the full-scope backend repository.

---

## Diagnostic Pipeline

The backend processes image batches through a two-stage hybrid pipeline:

1. **Deterministic Analysis.** The IlluminationAnalyzer extracts luminance-based metrics from each frame. The Rule Engine maps these metrics to a structured diagnostic output: pass/fail status, risk level, and triggered rules. This stage completes in under 20 ms per frame regardless of hardware or model.

2. **Language-Based Explanation.** A Small Language Model generates a concise natural language explanation for each frame and a scene-level summary for the batch. If the model output fails validation, the system falls back to deterministic template explanations, guaranteeing a valid response regardless of model behavior.

**Key design principle:** the Rule Engine provides deterministic and fully traceable decisions. The SLM generates user-facing explanations without affecting the diagnostic outcome.

---

## Evaluated Models

| Model | Parameters | Platforms | Notes |
|---|---|---|---|
| DialoGPT-small | 117M | All | Only viable model on Jetson Nano native stack |
| Qwen2.5-0.5B | 0.5B | Orin, Legion | Best latency/quality trade-off |
| Phi-3 Mini | 3.8B | Orin, Legion | Best explanation quality |

See [docs/MODEL_SELECTION.md](docs/MODEL_SELECTION.md) for platform recommendations and detailed benchmark comparison.

---

## Performance

On the Desktop Legion and Jetson AGX Orin, all evaluated models achieve mean SLM latency below 0.8 s per diagnosis. On the Jetson Nano, DialoGPT-small achieves sub-second GPU-accelerated inference under the official NVIDIA stack.

| Platform | Model | Mean Latency |
|---|---|---:|
| Desktop Legion | DialoGPT-small | 0.056 s | 
| Desktop Legion | Qwen2.5-0.5B | 0.371 s | 
| Desktop Legion | Phi-3 Mini | 0.770 s | 
| Jetson AGX Orin | DialoGPT-small | 0.125 s | 
| Jetson AGX Orin | Qwen2.5-0.5B | 0.373 s | 
| Jetson AGX Orin | Phi-3 Mini | 0.679 s | 
| Jetson Nano (native) | DialoGPT-small | 0.363 s |
| Jetson Nano (Ubuntu 20.04) | Qwen GPU | 2.911 s | 

For a full analysis including batch efficiency, the amortization model, and applied optimizations, see [docs/BATCH_PERFORMANCE.md](docs/BATCH_PERFORMANCE.md).

### Jetson Nano: Deployment Investigation

The Jetson Nano results above represent the outcome of a non-trivial deployment process. The details are documented here because the failure modes encountered are subtle and practically important for anyone working with modern AI frameworks on legacy embedded hardware.

**Initial attempt: Docker with Python 3.8**

Early experiments used a Docker-based environment with Python 3.8 to work around the native JetPack 4.6 Python 3.6 limitation. The pipeline appeared to run correctly, but exhibited unexpectedly high latency well above what the hardware should theoretically support. Rather than accepting this as a hardware limitation, the Jetson AGX Orin was used as a reference platform to validate the pipeline under known-good conditions.

**Key insight from the Orin**

Working with the Orin revealed a recurring pattern: automatic dependency resolution via Poetry consistently produced conflicts between PyTorch, CUDA, and the transformer libraries. The solution was a manually sequenced installation that installs packages in a specific order to ensure compatibility. This insight proved to be the turning point for the Nano as well.

**Root cause: silent CPU fallback**

Applying the same manual installation strategy to the Nano and verifying GPU activation explicitly revealed the root cause of the earlier slowness: the pipeline had been running entirely on CPU throughout the Docker experiments. Architecture incompatibilities inside the container caused a silent fallback: `torch.cuda.is_available()` returned `False` inside the container, but this was never surfaced as an error. The pipeline continued running, just at CPU speeds.

This is a subtle and practically important failure mode: the system produces correct results at greatly degraded performance, with no obvious error signal. Explicit GPU verification at startup is now built into all setup scripts in this repository.

**Resolution: official NVIDIA JetPack stack**

Switching to the official NVIDIA stack (JetPack 4.6, Python 3.6, CUDA 10.2) with the manually sequenced installation resolved GPU execution for DialoGPT-small, whose architecture is fully compatible with this legacy environment. Under this configuration, DialoGPT-small achieves 0.363 s mean latency and 2.76 diagnoses/s throughput, comfortably meeting the 1.0 s target.

**Running Qwen on the Nano**

Qwen2.5-0.5B requires a newer Python and Transformers stack than the official JetPack 4.6 environment can support. Running it with GPU acceleration required installing a community-maintained Ubuntu 20.04 image directly on a second Nano unit, which provides a modern enough userspace while retaining CUDA access. Under this configuration, Qwen latency drops from 15.388 s on CPU to 2.911 s on GPU, a 5.3x speedup. Latency also varies with diagnostic complexity: well-lit batches complete in approximately 16 s, while underexposed scenes can reach 56 s, compared to over 190 s for the CPU equivalent.

Phi-3 Mini could not be loaded on the Nano under any configuration; its memory requirements exceed the 4 GB VRAM budget.

**What this means in practice**

Achieving GPU-accelerated inference for a modern 0.5B-parameter model on legacy embedded hardware is a meaningful engineering result in its own right. The engineering effort required to bridge the gap between modern AI frameworks and legacy embedded platforms should not be underestimated, and the gap is not always visible until GPU activation is explicitly verified.

For setup instructions per platform, see [docs/PLATFORM_SETUP.md](docs/PLATFORM_SETUP_GUIDE.md).

---

## Hardware Platforms

| Platform | GPU | VRAM | CUDA | PyTorch |
|---|---|---|---|---|
| Desktop Legion | RTX 3060 | 6 GB | 12.1 | 2.5 |
| Jetson AGX Orin | Ampere | 32 GB | 12.x | 2.x |
| Jetson Nano | Maxwell | 4 GB | 10.2 | 1.10 |

---

## Quick Start

### Desktop NVIDIA GPU (Ubuntu, Windows, CUDA 12.8 wheel)

Ubuntu:

```bash
bash setup_desktop_gpu.sh
poetry run ar-api
```

Windows PowerShell:

```powershell
.\setup_legion.ps1
poetry run ar-api
```

### Jetson AGX Orin (JetPack 6.x)

```bash
bash setup_jetson_orin.sh
poetry run ar-api
```

### Jetson Nano (JetPack 4.6, native)

```bash
export OPENBLAS_CORETYPE=ARMV8
bash setup_poetry_nano.sh
poetry run ar-api
```

For detailed setup instructions, troubleshooting, and YAML configuration per platform, see [docs/PLATFORM_SETUP.md](docs/PLATFORM_SETUP_GUIDE.md).

---

## REST API

The backend exposes a two-step REST API. Images are uploaded first, then diagnosed in a separate request. This separation keeps PDI extraction and SLM inference independent, enabling better error isolation per frame.

```
POST /upload/batch                         upload N images, get batch_id
POST /diagnose/batch/{batch_id}            run diagnosis on saved batch
GET  /diagnose/batch/{batch_id}/status     check progress
GET  /diagnose/batch/{batch_id}/result     retrieve saved result
GET  /health                               API status and model info
```

After starting the API, interactive documentation is available at `http://localhost:8000/docs`.

For endpoint details, request/response schemas, and usage examples, see [docs/API_GUIDE.md](docs/API_GUIDE.md).

---

## Project Structure

```
backend_tcc_mvp/
├── app/
│   ├── api/            FastAPI application and HTTP routes
│   ├── config/         Configuration loader and YAML files
│   ├── core/           Rule engine and output validators
│   ├── models/         SLM implementations (DialoGPT, Qwen, Phi-3)
│   ├── pdi/            Illumination analyzer
│   ├── pipeline/       End-to-end diagnostic pipeline
│   └── utils/          Fallback explanation templates
├── benchmarks/         Benchmark plotting scripts and outputs
├── data/               Input images for validation and testing
├── outputs/            Benchmark result JSON files by platform
├── docs/               Technical documentation
├── setup_legion.ps1
├── setup_jetson_orin.sh
├── setup_poetry_nano.sh
├── pyproject-legion.toml
├── pyproject-jetson-orin.toml
└── pyproject-jetson-nano.toml
```

---

## Documentation

| File | Description |
|---|---|
| [docs/PLATFORM_SETUP.md](docs/PLATFORM_SETUP.md) | Platform-specific setup instructions |
| [docs/MODEL_SELECTION.md](docs/MODEL_SELECTION.md) | Model comparison and selection guidance |
| [docs/API_GUIDE.md](docs/API_GUIDE.md) | API endpoints, schemas, and usage examples |
| [docs/BATCH_PERFORMANCE.md](docs/BATCH_PERFORMANCE.md) | Batch inference analysis with performance results |
| [docs/STRUCTURE.md](docs/STRUCTURE.md) | Repository organization |

---

## Research and Academic Context

This project was developed as the final project for the **Robotics and Artificial Intelligence Residency / Postgraduate Program at CIn-UFPE**, Cohort 4, investigating hybrid scene diagnosis pipelines for augmented reality on embedded systems.

The main contributions are:

1. A hybrid diagnostic pipeline combining deterministic analysis, rule-based classification, and Small Language Model inference
2. End-to-end deployment and validation across three heterogeneous embedded platforms
3. An interpretable methodology for evaluating environmental conditions in AR applications

---

## Author

**Daniela Amorim de Sá**  
Electronic Engineer, Universidade Federal de Pernambuco (UFPE)  
Robotics and Artificial Intelligence Residency / Postgraduate Program, CIn-UFPE, Cohort 4  
GitHub: [@daniamorimdesa](https://github.com/daniamorimdesa)  
Email: [daniela.amorimdesa@gmail.com](mailto:daniela.amorimdesa@gmail.com)

---

## License

This project is released under the **MIT License**. See [LICENSE](LICENSE) for details.