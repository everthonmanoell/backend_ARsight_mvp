# Batch Inference Performance

This document summarizes batch inference behavior and performance results for the AR Diagnostic MVP across the three evaluated hardware environments.

---

## Model Compatibility by Platform

| Platform | Supported Models | Constraint |
|---|---|---|
| Desktop Legion | Qwen2.5-0.5B, Phi-3 Mini, DialoGPT-small | None |
| Jetson AGX Orin | Qwen2.5-0.5B, Phi-3 Mini, DialoGPT-small | None |
| Jetson Nano (native) | DialoGPT-small only | Python 3.6 / PyTorch 1.10 legacy stack |
| Jetson Nano (Ubuntu 20.04) | Qwen2.5-0.5B | Non-standard community image required |

---

## How Batch Inference Reduces Latency

Decoder-only models (GPT, Qwen, Phi) generate tokens sequentially: each token depends on all previous ones, so there is no parallelism within a single prompt. However, multiple prompts can be processed in parallel on the GPU within a single forward pass.

The total batch processing time follows an approximately linear model:

$$t_{\text{total}}(N) \approx t_1 + \alpha \cdot (N - 1)$$

where $t_1$ is the latency of a single isolated prompt and $\alpha$ is the marginal cost per additional prompt in the batch. Because $\alpha \ll t_1$, the per-diagnosis cost decreases as batch size grows:

$$t_{\text{diag}}(N) = \frac{t_{\text{total}}(N)}{N} = \frac{t_1 + \alpha \cdot (N-1)}{N}$$

As $N \to \infty$, $t_{\text{diag}}(N) \to \alpha$. In practice, the gains plateau at moderate batch sizes (3–6 frames in the evaluated setup), after which memory pressure and padding overhead offset the remaining benefit.

---

## Performance Results

### Desktop Legion

| Model | Mean Latency per Diagnosis |
|---|---:|
| DialoGPT-small | 0.056 s |
| Qwen2.5-0.5B | 0.371 s |
| Phi-3 Mini | 0.770 s |

All three models meet the 1.0 s latency target on the Desktop Legion environment.

### Jetson AGX Orin

| Model | Mean Latency per Diagnosis |
|---|---:|
| DialoGPT-small | 0.125 s |
| Qwen2.5-0.5B | 0.373 s |
| Phi-3 Mini | 0.679 s |

All three models meet the 1.0 s latency target on Jetson AGX Orin.

### Jetson Nano — Native (JetPack 4.6)

| Model | Mean Latency | Throughput |
|---|---:|---:|
| DialoGPT-small | 0.363 s | 2.76 diagnoses/s |

DialoGPT-small is the only supported model in the native JetPack 4.6 environment and comfortably meets the latency target.

### Jetson Nano — Ubuntu 20.04 (Qwen Experiment)

| Mode | Mean Latency |
|---|---:|
| Qwen CPU | 15.388 s |
| Qwen GPU | 2.911 s |

GPU activation via the community Ubuntu 20.04 image yields a 5.3× speedup over CPU execution. Even with GPU acceleration, Qwen latency on the Nano exceeds the 1.0 s target, making DialoGPT-small the recommended production model for this platform.

---

## Applied Optimizations

| Optimization | Effect | Platforms |
|---|---|---|
| Warmup on startup (3 forward passes) | Eliminates first-request latency spike | All |
| True batch inference | Amortizes setup overhead across N prompts | All |
| `padding_side='left'` | Prevents quality degradation in batched generation | All |
| 4-bit NF4 quantization | ~75% VRAM reduction; enables larger batch sizes | Desktop Legion, Jetson AGX Orin |

---

## Request Flow: `/diagnose/batch`

```
POST /diagnose/batch  (N JPEG images)
  |
  +-- Input validation             (~1 ms)
  |
  +-- PDI / IlluminationAnalyzer   (~5-20 ms per image)
  |   Computes luminance score and illumination label per frame
  |   Labels: underexposed | acceptable | adequate | overexposed
  |
  +-- Rule Engine                  (<1 ms, deterministic)
  |   Thresholds -> status + risk_level + triggered_rules
  |
  +-- SLM Batch Inference
  |   Desktop Legion:   Qwen 0.371 s/diag | Phi 0.770 s/diag | DialoGPT 0.056 s/diag
  |   Jetson AGX Orin:  Qwen 0.373 s/diag | Phi 0.679 s/diag | DialoGPT 0.125 s/diag
  |   Jetson Nano:      DialoGPT 0.363 s/diag
  |
  +-- Output validation + template fallback if needed
  |
  +-- JSON response
      Per frame: status, risk_level, explanation, metrics, recommendations
      Environment-level: summary, dominant condition, aggregated metrics
```