# Model Selection — AR Diagnostic MVP

This document summarizes the language models evaluated in the project, their main characteristics, hardware requirements, and recommended usage across the validated execution environments.

The project considered three model families:

- DialoGPT-small
- Qwen2.5-0.5B
- Phi-3-mini

The final recommendation depends on the target platform and the trade-off between latency, compatibility, and explanation quality.

## Model Comparison

| Aspect | DialoGPT-small | Qwen2.5-0.5B | Phi-3-mini |
|---|---|---|---|
| Model family | Conversational | Instruction-tuned | Instruction-tuned |
| Size | 117M params | ~0.5B params | ~3.8B params |
| Typical VRAM footprint (FP16) | Low | Moderate | High |
| Explanation quality | Acceptable | Strong | Best |
| Latency | Lowest | Moderate | Highest |
| Jetson Nano | ✅ Supported | ❌ Not supported in validated stack | ❌ Not supported |
| Jetson AGX Orin | ✅ Supported | ✅ Recommended | ✅ Optional |
| Desktop Legion | ✅ Supported | ✅ Recommended | ✅ Recommended |


## 1. DialoGPT-small

### Characteristics

- Lightweight conversational model
- Very low memory footprint
- Fastest inference among the evaluated options
- Suitable for highly constrained embedded environments

### Recommended usage

- Jetson Nano: default and validated choice
- Fast prototyping
- Baseline latency measurements
- Scenarios where low latency is more important than maximum explanation quality

### Main limitation

- Lower explanation quality than Qwen and Phi
- Requires stronger prompt control and validation to avoid conversational drift

### Typical role in the project

DialoGPT-small was the validated model for Jetson Nano, where software-stack and hardware constraints made larger models impractical.

### Example configuration

```yaml
models:
  default: dialogpt-small
  device: cuda
  use_4bit: false
  greedy_decoding: true
  prompt_max_length: 256
  warmup_on_startup: true

  dialogpt-small:
    name: /home/das9/models/DialoGPT-small
    max_tokens: 20
    summary_tokens: 32
    temperature: 0.3
    top_p: 0.85
```


## 2. Qwen2.5-0.5B

### Characteristics

- Instruction-tuned model
- Better prompt following than DialoGPT-small
- Better explanation quality for the diagnostic task
- Good trade-off between quality and latency on modern platforms

### Recommended usage

- Jetson AGX Orin: recommended default choice
- Desktop Legion: recommended for production and benchmarks
- General-purpose deployment when explanation quality matters and latency must remain practical

### Main limitation

- Not supported in the validated Jetson Nano stack
- Requires a newer software stack than the one stabilized for JetPack 4.6 / Python 3.6

### Important note on Jetson Nano

Although Qwen2.5-0.5B is much smaller than Phi-3-mini, it was not supported in the final validated Nano setup.
The issue was not only memory pressure, but also software-stack compatibility.

### Typical role in the project

Qwen2.5-0.5B became the main recommendation for Orin and Legion, offering the best balance between throughput and explanation quality.

### Example configuration

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
```


## 3. Phi-3-mini

### Characteristics

- Highest reasoning and explanation quality among the evaluated models
- Strong instruction following
- Best option when textual quality is prioritized over latency

### Recommended usage

- Jetson AGX Orin: optional, when quality is prioritized
- Desktop Legion: recommended when latency budget allows it
- Comparative evaluation against smaller models

### Main limitation

- Higher latency than Qwen
- Higher memory consumption
- Not suitable for Jetson Nano

### Typical role in the project

Phi-3-mini was evaluated as the highest-quality option, especially relevant in Orin and Legion experiments, but with a clear cost in inference time.

### Example configuration

```yaml
models:
  default: phi
  device: cuda
  use_4bit: false
  greedy_decoding: false
  prompt_max_length: 512
  warmup_on_startup: true

  phi:
    name: microsoft/Phi-3-mini-4k-instruct
    max_tokens: 120
    summary_tokens: 200
    temperature: 0.3
    top_p: 0.85
```

## Platform Decision Matrix

### Jetson Nano

**Recommended model:** DialoGPT-small

**Reason:**

- validated with the final stable Nano stack
- compatible with JetPack 4.6 / Python 3.6 / PyTorch 1.10
- acceptable latency for embedded deployment

**Not recommended:**

- Qwen2.5-0.5B → unsupported in the validated Nano stack
- Phi-3-mini → exceeds practical memory / latency constraints

### Jetson AGX Orin

**Recommended default model:** Qwen2.5-0.5B

**Reason:**

- strong explanation quality
- practical latency
- better trade-off for deployment

**Alternative:** Phi-3-mini

**Reason:**

- better textual quality
- useful when explanation quality is more important than throughput

### Desktop Legion

**Recommended default model:** Qwen2.5-0.5B

**Reason:**

- best overall balance for production-style runs and benchmarks

**Quality-oriented option:** Phi-3-mini

**Reason:**

- strong explanation quality
- desktop environment tolerates higher inference cost better than embedded platforms

**Fast baseline:** DialoGPT-small

**Reason:**

- useful as lightweight reference model

## Recommended Summary by Platform

| Platform | Recommended model | Why |
|---|---|---|
| Jetson Nano | DialoGPT-small | Only model validated in the final Nano stack |
| Jetson AGX Orin | Qwen2.5-0.5B | Best latency/quality trade-off |
| Desktop Legion | Qwen2.5-0.5B | Best overall balance |
| Desktop Legion (quality-first) | Phi-3-mini | Best explanation quality |

## Selection Guidelines

**Choose DialoGPT-small when:**

- the target platform is Jetson Nano
- latency is the highest priority
- the environment is highly constrained
- a lightweight baseline is needed

**Choose Qwen2.5-0.5B when:**

- explanation quality matters more than minimal latency
- the target platform is Orin or Legion
- you want the best practical trade-off

**Choose Phi-3-mini when:**

- explanation quality is the top priority
- the platform has enough memory and compute budget
- higher latency is acceptable

## Practical Notes

- Jetson Nano should be treated as a constrained deployment target, not as a general-purpose LLM platform.
- Jetson AGX Orin supports modern models more comfortably, but still involves embedded-system trade-offs.
- Desktop Legion offers the most flexible environment for experiments and high-quality inference.

For exact benchmark values, refer to the measurement outputs stored in the repository under the benchmark and platform-specific output folders.

## Useful Links

- [DialoGPT-small](https://huggingface.co/microsoft/DialoGPT-small)
- [Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)
- [Phi-3-mini-4k-instruct](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct)
- [PyTorch Documentation](https://pytorch.org/)
