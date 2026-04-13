# Seleção de Modelos — AR Diagnostic MVP

Este documento explica os 3 modelos de linguagem disponíveis no projeto, suas características, requisitos de hardware, e quando usar cada um.

## 📊 Comparação dos Modelos

| Aspecto | **DialoGPT-small** | **Qwen2.5-0.5B** | **Phi-3-mini** |
|---|---|---|---|
| **Tamanho** | 117M params | 494M params | 3.8B params |
| **VRAM (FP16)** | ~250 MB | ~1 GB | ~7.6 GB |
| **Latência (Nano)** | ~250 ms/frame | ~500 ms/frame | ❌ Não cabe |
| **Latência (Orin)** | ~150 ms/frame | ~300 ms/frame | ~800 ms/frame |
| **Latência (Legion RTX)** | ~50 ms/frame | ~100 ms/frame | ~300 ms/frame |
| **Qualidade** | Boa (tuned) | Excelente | Excelente |
| **Tipo** | Conversacional | Instruct | Instruct |
| **Jetson Nano** | ✅ Obrigatório | ❌ Incompatível | ❌ Sem espaço |
| **Jetson Orin** | ✅ Funciona | ✅ Trade-off: Rápido | ✅ Trade-off: Qualidade |
| **Legion (RTX)** | ✅ Funciona | ✅ Trade-off: Rápido | ✅ Trade-off: Qualidade |

---

## 1️⃣ DialoGPT-small (Microsoft)

### Características
- **Conversacional** — treinado em diálogos
- **Ultracompacto** — 117M params, ~250 MB
- **Rápido** — ideal para edge computing
- **Determinístico** — com `greedy_decoding=true`

### Quando usar
- ✅ Jetson Nano (única opção com CUDA viável)
- ✅ Testes rápidos de prototipagem
- ✅ Quando latência < 500 ms é crítico
- ❌ Quando qualidade máxima é necessária

### Configuração YAML
```yaml
models:
  default: dialogpt
  device: cuda              # GPU quando disponível
  precision: fp16           # Reduz consumo de memória
  
dialogpt_config:
  model_name: "microsoft/DialoGPT-small"
  prompt_max_length: 256
  max_tokens: 20            # Per-frame
  summary_tokens: 32
  temperature: 0.3
  top_p: 0.85
  greedy_decoding: true
```

### Performance no Jetson Nano
```
Tempo total (batch 10 frames): ~3.4s
- PDI (rule engine): ~91 ms/frame
- DialoGPT inference: ~250 ms/frame (total)
```

### Validação
```bash
poetry run python -c "
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = 'microsoft/DialoGPT-small'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name).cuda()

input_ids = tokenizer.encode('Hello', return_tensors='pt').cuda()
output = model.generate(input_ids, max_length=20)
print('✅ DialoGPT working')
"
```

---

## 2️⃣ Qwen2.5-0.5B (Alibaba)

### Características
- **Instrução-tuned** — segue prompts melhor que DialoGPT
- **Qualidade superior** — melhor compreensão de contexto
- **Compacto** — 494M params, ~1 GB em FP16
- **Multilíngue** — suporta 30+ idiomas

### Quando usar
- ✅ Jetson Nano com budget de latência (500-600 ms ok)
- ✅ Jetson Orin/RTX quando qualidade > velocidade (trade-off: 2-3x mais lento que Phi)
- ✅ Quando a qualidade de respostas é mais importante
- ❌ Se precisar máxima latência (< 300 ms)

### Configuração YAML
```yaml
models:
  default: qwen
  device: cuda
  precision: fp16
  
qwen_config:
  model_path: "/home/das9/models/Qwen2.5-0.5B-Instruct"  # Local cache
  prompt_max_length: 128
  max_tokens: 20
  summary_max_tokens: 32
  temperature: 0.2
  top_p: 0.9
  greedy_decoding: true
```

### Performance

**Jetson Nano:**
```
Tempo total (batch 10 frames): ~5-6s
- PDI: ~91 ms/frame
- Qwen inference: ~500 ms/frame (total)
Target: 3.5s ❌ (exceeds for Nano)
```

**Jetson Orin:**
```
Tempo total (batch 10 frames): ~3-4s
- PDI: ~50 ms/frame
- Qwen inference: ~250 ms/frame (total)
Target: 3.5s ✅
```

### Validação
```bash
poetry run python -c "
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

model_path = '/home/das9/models/Qwen2.5-0.5B-Instruct'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path).cuda()

input_ids = tokenizer.encode('Brightness:', return_tensors='pt').cuda()
output = model.generate(input_ids, max_length=20)
print('✅ Qwen working')
"
```

---

## 3️⃣ Phi-3-mini (Microsoft)

### Características
- **Alta qualidade** — 3.8B params
- **Instruct-tuned** — segue instruções complexas
- **Inteligente** — melhor raciocínio que Qwen 0.5B
- **Pesado** — ~7.6 GB em FP16

### Quando usar
- ✅ Jetson Orin/RTX quando qualidade máxima é necessária (trade-off: até 3x mais lento que Qwen)
- ✅ Quando o sistema pode tolerar latência ~300-800 ms
- ❌ Jetson Nano (sem espaço VRAM)
- ❌ Quando latência é crítico (< 300 ms)

### Configuração YAML
```yaml
models:
  default: phi
  device: cuda
  precision: fp16
  
phi_config:
  model_name: "microsoft/Phi-3-mini-4k-instruct"
  prompt_max_length: 256
  max_tokens: 32
  summary_max_tokens: 64
  temperature: 0.7
  top_p: 0.95
  greedy_decoding: false
```

### Performance

**Jetson Orin:**
```
Tempo total (batch 10 frames): ~8-10s
- PDI: ~50 ms/frame
- Phi inference: ~800 ms/frame (total)
Target: 3.5s ❌ (muito lento para uso produção)
```

**Legion RTX 3080:**
```
Tempo total (batch 10 frames): ~3-4s
- PDI: ~10 ms/frame
- Phi inference: ~300 ms/frame (total)
Target: 3.5s ✅ (aceita)
```

### Validação
```bash
poetry run python -c "
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = 'microsoft/Phi-3-mini-4k-instruct'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name).cuda()

input_ids = tokenizer.encode('Analyze:', return_tensors='pt').cuda()
output = model.generate(input_ids, max_length=32)
print('✅ Phi-3 working')
"
```

---

## 🎯 Matriz de Decisão

### Jetson Nano (4GB VRAM)
```
┌─────────────────────────────────┐
│  Jetson Nano – Escolha de Modelo │
└─────────────────────────────────┘

Priority: Latência (< 3.5s)?
├─ SIM → Usar DialoGPT-small ✅
│        Tempo: ~3.4s
│        Qualidade: Boa (tuned para iluminação)
│
└─ NÃO (qualidade > speed)?
   ├─ Qwen 0.5B (experimentar)
   │  Tempo: ~5-6s ⚠️
   │  Qualidade: Excelente
   │
   └─ Phi-3 ❌
      Memória: Não cabe
```

### Jetson Orin (32GB VRAM)
```
┌─────────────────────────────────┐
│  Jetson Orin – Escolha de Modelo │
└─────────────────────────────────┘

Priority: Performance vs Qualidade?
├─ Speed (3s baseline) → Qwen 0.5B ✅
│  Tempo: ~3.5s
│  Qualidade: Excelente
│
├─ Quality (< 5s ok) → Phi-3 ✅
│  Tempo: ~8-10s
│  Qualidade: Superior
│
└─ Best of Both → Qwen 0.5B (recomendado)
```

### Legion Windows (RTX 3080+)
```
┌────────────────────────────────┐
│ Legion RTX – Escolha de Modelo │
└────────────────────────────────┘

Recomendado: Phi-3-mini ✅
├─ Tempo: ~3-4s (muito rápido)
├─ Qualidade: Superior
├─ Custo: Baixo (offline)
│
Alternativas:
├─ Qwen 0.5B (mais rápido ainda: ~1s)
└─ DialoGPT-small (ultrarrápido: ~0.5s)
```

---

## 🔧 Como Trocar Modelos

### 1. Editar `app/config/thresholds.yaml`

```yaml
# Antes (DialoGPT)
models:
  default: dialogpt

# Depois (Qwen)
models:
  default: qwen
```

### 2. Copiar modelo se necessário

```bash
# Para Qwen (já em cache na Nano)
mkdir -p ~/.cache/huggingface/hub
cp -r /path/to/Qwen2.5-0.5B-Instruct ~/.cache/huggingface/hub/

# Para Phi (download automático na primeira execução)
# Requer ~8 GB de espaço livre
```

### 3. Rodar com novo modelo

```bash
# Poetry
poetry run ar-api

# Docker
docker-compose up --build
```

---

## 📌 Resumo Recomendado

| Ambiente | Modelo | Razão |
|---|---|---|
| **Jetson Nano** | DialoGPT-small | Único que cabe com latência < 3.5s |
| **Jetson Orin** | Qwen 0.5B | Qualidade excelente + latência aceitável |
| **Legion RTX** | Phi-3-mini | Melhor qualidade + tempo rápido |

---

## 🔗 Links úteis

- [DialoGPT - Hugging Face](https://huggingface.co/microsoft/DialoGPT-small)
- [Qwen2.5-0.5B - Hugging Face](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)
- [Phi-3-mini - Hugging Face](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct)
- [Otimização de modelos - PyTorch](https://pytorch.org/docs/stable/quantization.html)
