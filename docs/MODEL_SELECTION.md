# Model Selection Guide

This document summarizes the Small Language Models evaluated in the AR Diagnostic MVP and provides practical guidance for selecting a model according to the target platform.

The project evaluated three model families:

- DialoGPT-small
- Qwen2.5-0.5B-Instruct
- Phi-3 Mini

The final choice depends on the trade-off between latency, compatibility, memory usage, and explanation quality.

## Model Overview

| Model | Size | Main Strength | Main Limitation | Best Use |
|---|---:|---|---|---|
| DialoGPT-small | 117M | Very low latency and memory usage | Lower explanation quality | Constrained environments and baseline tests |
| Qwen2.5-0.5B | 0.5B | Best latency/quality balance | Requires newer software stack | Main MVP model on Orin and desktop |
| Phi-3 Mini | 3.8B | Best explanation quality | Higher memory and latency cost | Quality-oriented runs on Orin/desktop |

## Platform Recommendations

| Platform | Recommended Model | Alternative | Notes |
|---|---|---|---|
| Desktop Legion | Qwen2.5-0.5B | Phi-3 Mini, DialoGPT-small | All evaluated models run within practical latency bounds |
| Jetson AGX Orin | Qwen2.5-0.5B | Phi-3 Mini, DialoGPT-small | Supports the full evaluated model range |
| Jetson Nano native | DialoGPT-small | None recommended | Official JetPack 4.6 stack is limited to legacy-compatible models |
| Jetson Nano Ubuntu 20.04 | Qwen2.5-0.5B | DialoGPT-small | Non-standard setup used for Qwen GPU experiments |

## Desktop Legion

The Desktop Legion environment is used as the development and reference benchmark platform. All three evaluated models run below the 1.0 s latency target:

| Model | Mean Latency |
|---|---:|
| DialoGPT-small | 0.056 s |
| Qwen2.5-0.5B | 0.371 s |
| Phi-3 Mini | 0.770 s |

Qwen2.5-0.5B is the recommended default because it provides the best balance between latency and explanation quality. Phi-3 Mini can be used when textual quality is prioritized. DialoGPT-small is useful as a lightweight baseline.

## Jetson AGX Orin

Jetson AGX Orin supports the full evaluated model range within practical latency limits:

| Model | Mean Latency |
|---|---:|
| DialoGPT-small | 0.125 s |
| Qwen2.5-0.5B | 0.373 s |
| Phi-3 Mini | 0.679 s |

Qwen2.5-0.5B is the recommended default for Orin because it maintains strong explanation quality while preserving low latency. Phi-3 Mini is viable when higher-quality explanations are needed and the latency budget allows it.

## Jetson Nano

Jetson Nano requires separate consideration because model feasibility depends strongly on the software stack.

### Native JetPack 4.6 Setup

The official JetPack 4.6 environment uses a legacy stack:

- Python 3.6.9
- CUDA 10.2
- PyTorch 1.10.0 NVIDIA wheel

In this setup, DialoGPT-small is the recommended model. It is compatible with the native Nano stack and meets the latency target:

| Model | Mean Latency | Throughput |
|---|---:|---:|
| DialoGPT-small | 0.363 s | 2.76 diagnoses/s |


### Ubuntu 20.04 Community Image

Qwen2.5-0.5B was also tested on Jetson Nano using a community Ubuntu 20.04 image. This setup provides a newer userspace while preserving GPU access. Under this configuration, Qwen latency improved from CPU-only execution to GPU-accelerated execution:

| Mode | Mean Latency |
|---|---:|
| Qwen CPU | 15.388 s |
| Qwen GPU | 2.911 s |


## Summary

Qwen2.5-0.5B is the main model selected for the MVP because it provides the best overall latency/quality trade-off on the primary target platforms. Phi-3 Mini is useful as a higher-quality but heavier alternative. DialoGPT-small remains important as an ultra-lightweight baseline and as the most practical model for native Jetson Nano execution.