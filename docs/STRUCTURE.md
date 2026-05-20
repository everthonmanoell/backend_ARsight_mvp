# Project Structure

This document summarizes the main structure of the AR Diagnostic MVP backend.

The project implements a hybrid scene diagnosis pipeline that combines deterministic illumination analysis with Small Language Model (SLM) explanations.

## Directory Overview

```text
backend_tcc_mvp/
│
├── app/
│   ├── api/
│   │   ├── main.py
│   │   └── routes.py
│   │
│   ├── config/
│   │   ├── config.py
│   │   ├── thresholds.yaml
│   │   └── thresholds.jetson.yaml
│   │
│   ├── core/
│   │   ├── rule_engine.py
│   │   └── validators.py
│   │
│   ├── models/
│   │   ├── base_model.py
│   │   ├── dialogpt_model.py
│   │   ├── phi_model.py
│   │   └── qwen_model.py
│   │
│   ├── pdi/
│   │   └── illumination.py
│   │
│   ├── pipeline/
│   │   └── illumination_pipeline.py
│   │
│   └── utils/
│       └── templates.py
│
├── benchmarks/
│   ├── generate_plots.sh
│   ├── plots_scripts/
│   └── plots_output/
│
├── data/
│   ├── illumination/
│   └── uploads/
│
├── outputs/
│   ├── desktop-legion/
│   ├── jetson-nano/
│   └── jetson-orin/
│
├── docker/
│   └── Dockerfile.jetson-nano
│
├── docs/
│   ├── API_GUIDE.md
│   ├── BATCH_PERFORMANCE.md
│   ├── MODEL_SELECTION.md
│   ├── PLATFORM_SETUP.md
│   └── STRUCTURE.md
│
├── docker-compose.yml
├── requirements-jetson.txt
├── pyproject-legion.toml
├── pyproject-jetson-nano.toml
├── pyproject-jetson-orin.toml
├── setup_legion.ps1
├── setup_jetson_orin.sh
├── setup_poetry_nano.sh
└── README.md
```

## Main Application Modules

### app/api/

Contains the FastAPI application and HTTP routes.

- **main.py**: creates the FastAPI application, configures startup behavior, and registers routes.
- **routes.py**: defines endpoints for health checks, uploads, metric extraction, and diagnosis.

### app/config/

Contains configuration loading and YAML files.

- **config.py**: central configuration helper.
- **thresholds.yaml**: general configuration used across all validated platforms.
- **thresholds.jetson.yaml**: configuration used in the early Docker-based Nano experiment.

### app/core/

Contains deterministic logic and validation utilities.

- **rule_engine.py**: converts illumination metrics into diagnostic status, risk level, triggered rules, and recommendations.
- **validators.py**: validates SLM outputs and metric dictionaries, rejecting malformed, generic, or out-of-scope explanations.

### app/models/

Contains the SLM implementations.

- **base_model.py**: abstract base class implementing the hybrid flow: Rule Engine + SLM + validation + template fallback.
- **qwen_model.py**: Qwen2.5-0.5B-Instruct implementation.
- **phi_model.py**: Phi-3 Mini implementation.
- **dialogpt_model.py**: DialoGPT-small implementation.

For model recommendations by platform, see [MODEL_SELECTION.md](MODEL_SELECTION.md).

### app/pdi/

Contains deterministic image-processing components.

- **illumination.py**: extracts luminance-based metrics from images, including illumination score and classification.

### app/pipeline/

Contains the end-to-end diagnostic pipeline.

- **illumination_pipeline.py**: orchestrates illumination analysis and SLM-based diagnostic generation.

### app/utils/

Contains support utilities.

- **templates.py**: deterministic fallback explanation templates used when SLM generation fails or is rejected by validation.

## Benchmark Modules

The benchmarks/ directory contains scripts used to aggregate benchmark outputs and generate thesis figures.

```text
benchmarks/
├── generate_plots.sh
├── plots_scripts/
│   ├── arsight_theme.py
│   ├── data_loader.py
│   ├── generate_all.py
│   ├── generate_ycbcr_visualization.py
│   ├── plot_01_env_performance.py
│   ├── plot_02_model_comparison.py
│   ├── plot_03_accuracy_by_batch.py
│   ├── plot_04_latency_distribution.py
│   ├── plot_05_cross_env_speedup.py
│   ├── plot_06_pdi_vs_slm.py
│   ├── plot_07_jetson_nano_performance.py
│   ├── plot_08_jetson_orin_performance.py
│   ├── plot_09_desktop_legion_performance.py
│   └── plot_10_qwen_cpu_vs_gpu_nano.py
└── plots_output/
```

To regenerate all benchmark plots:

```bash
bash benchmarks/generate_plots.sh
```

Generated figures and the HTML report are saved to `benchmarks/plots_output/`.

## Data and Outputs

### data/

Contains input images used for validation, uploads, and laboratory test batches.

### outputs/

Contains benchmark result JSON files organized by execution platform:

```text
outputs/
├── desktop-legion/
├── jetson-nano/
└── jetson-orin/
```

These files are consumed by the benchmark plotting scripts.

## Platform Setup Files

Platform-specific setup instructions are documented in [PLATFORM_SETUP.md](PLATFORM_SETUP.md).

| File | Purpose |
|------|---------|
| setup_legion.ps1 | Desktop Legion setup |
| setup_jetson_orin.sh | Jetson AGX Orin setup |
| setup_poetry_nano.sh | Native Jetson Nano setup |
| docker/Dockerfile.jetson-nano | Early Docker-based Nano experiment (resulted in silent CPU fallback) |
| docker-compose.yml | Docker Compose used in early Nano experiment  |
| pyproject-legion.toml | Desktop Legion dependency configuration |
| pyproject-jetson-orin.toml | Jetson AGX Orin dependency configuration |
| pyproject-jetson-nano.toml | Native Jetson Nano dependency configuration |
| requirements-jetson.txt | Dependency list used in early Nano Docker experiment |

## Runtime Flow

The main diagnostic flow is:

```
HTTP request
  -> FastAPI route
  -> IlluminationPipeline
  -> IlluminationAnalyzer
  -> RuleEngine
  -> Selected SLM model
  -> OutputValidator
  -> Template fallback if needed
  -> JSON response
```

For batch diagnosis:

```
Uploaded image batch
  -> PDI metric extraction per frame
  -> batched SLM explanation generation
  -> environment-level summary
  -> recommendations grouped by illumination condition
```

## Documentation Files

| File | Purpose |
|------|---------|
| README.md | Main project overview |
| docs/API_GUIDE.md | API usage and endpoint examples |
| docs/PLATFORM_SETUP.md | Platform-specific setup instructions |
| docs/MODEL_SELECTION.md | Model comparison and selection guidance |
| docs/STRUCTURE.md | Repository organization |
| docs/BATCH_PERFORMANCE.md | Batch Inference with SLM |