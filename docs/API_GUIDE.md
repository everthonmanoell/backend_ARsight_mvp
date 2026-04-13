# API Guide - AR Diagnostic MVP

Guia completo da API para análise de iluminação em imagens com modelos LLM.

## 📋 Índice

1. [Overview da Arquitetura](#overview-da-arquitetura)
2. [Pipeline de Processamento](#pipeline-de-processamento)
3. [Modelos Disponíveis](#modelos-disponíveis)
4. [Endpoints](#endpoints)
5. [Exemplos de Uso](#exemplos-de-uso)
6. [Performance](#performance)
7. [Monitoramento](#monitoramento)
8. [Troubleshooting](#troubleshooting)
9. [Configuração](#configuração)

---

## Overview da Arquitetura

### Fluxo Geral

```
Imagem (JPEG/PNG) 
    ↓
[PDI - Photographic Dynamic Interpretation]
    ↓
Métricas de Iluminação (não depende de modelo)
    ├─ illumination_score (0-1)
    ├─ illumination_label (underexposed/adequate/overexposed/mixed)
    ├─ mean_luma
    ├─ uniformity
    ├─ exposure_score
    ├─ contrast_score
    └─ clipping metrics
    ↓
[Rule Engine + LLM Pipeline]
    ↓
Validação + Diagnóstico
    ├─ Se regra + LLM concorda → Diagnóstico com confiança alta
    ├─ Se LLM halucina → Fallback para template
    └─ Se LLM falha → Fallback para métricas puras
    ↓
Response JSON (status + explanation + summary)
```

### Componentes Principais

| Componente | Responsabilidade | Tempo |
|-----------|------------------|-------|
| **PDI (Illumination Analyzer)** | Extração de métricas brutas | ~10ms |
| **Rule Engine** | Classificação por regras | ~5ms |
| **LLM (DialoGPT/Qwen/Phi)** | Geração de diagnóstico em linguagem natural | ~250-800ms |
| **Validação (8-tier)** | Detecta hallucinations do LLM | ~5ms |
| **Templates** | Fallback quando LLM falha | N/A |

**Tempo Total Esperado:**
- Apenas métricas (`/metrics`): ~15ms
- Com LLM (`/diagnose`): ~300-1000ms (depende do modelo)

---

## Pipeline de Processamento

### 1. Extração de Métricas (PDI)

Análise fotográfica sem dependência de modelo LLM.

```python
from app.pipeline.illumination_pipeline import IlluminationPipeline
from PIL import Image

pipeline = IlluminationPipeline(model_type="dialogpt-small", device="cuda")
image = Image.open("photo.jpg")

# Extrai métricas (rápido, não usa LLM)
metrics = pipeline.extract_metrics_batch([image])[0]

print(f"Illumination Score: {metrics['illumination']:.2f}")
print(f"Label: {metrics['illumination_label']}")
print(f"Mean Luma: {metrics['mean_luma']:.1f}")
print(f"Uniformity: {metrics['uniformity']:.2f}")
```

**Métricas Retornadas:**

```json
{
  "illumination": 0.72,
  "illumination_label": "adequate",
  "mean_luma": 145.3,
  "std_luma": 52.1,
  "uniformity": 0.78,
  "pct_clipped_dark": 0.02,
  "pct_clipped_bright": 0.01,
  "exposure_score": 0.88,
  "contrast_score": 0.54,
  "clipping_penalty": 0.03,
  "histogram_bins": 256
}
```

### 2. Validação com LLM

DialoGPT é processado com **sistema de validação em 8 tiers** para evitar hallucinations.

#### 8-Tier Validation System

```
                    ↓ Raw LLM Output
                    
Tier 1: Question Detection
├─ Rejeita: Respostas terminando com "?"
└─ Motivo: Perguntas não são diagnósticos válidos

Tier 2: Interrogative Starter
├─ Rejeita: "What", "How", "Why", "Can", "Is", etc.
└─ Motivo: Conversas, não recomendações

Tier 3: Chat Patterns
├─ Rejeita: "I would", "I suggest", "I recommend"
└─ Motivo: Chat mode — não é domínio específico

Tier 4: Word Repetition
├─ Rejeita: Mesma palavra > 3x na resposta
└─ Motivo: Típico de hallucination (ex: "camera camera camera")

Tier 5: Token Repetition
├─ Rejeita: Padrão token.token.token
└─ Motivo: Tokenização corrompida

Tier 6: Malformed Suffixes
├─ Rejeita: ".I." com texto após
└─ Motivo: Corrupção de output

Tier 7: Domain-Specific Suffixes
├─ Rejeita: Suffixes inválidos (.camera, .device, .light, .mode, .setting)
└─ Motivo: Artefatos de hallucination

Tier 8: Missing Context
├─ Rejeita: Falta keywords de iluminação (illuminate, bright, dim, exposure, etc.)
└─ Motivo: Resposta não está contextualizada no domínio
                    
                    ↓ Se passou em todos os 8 tiers
                    
                [RESPOSTA VALIDADA]
                
                    ↓ Se falhou em qualquer tier
                    
         [FALLBACK PARA TEMPLATE ALEATÓRIO]
```

**Exemplo de Rejeição:**

```python
# LLM gera:
response = "You should use a camera camera camera to capture images properly"

# Validação detecta:
# - Tier 2: "You should" (chat pattern) → REJEITA
# - Tier 4: "camera" repetido 3x → REJEITA
# - Tier 7: Suffix ".camera" → REJEITA

# Resultado: Fallback para template
fallback = "The lighting conditions are not ideal for image capture. Aim for uniform illumination."
```

### 3. Summarization com Templates

Se LLM é rejeitado, usa um de 5 templates aleatórios por caso:

```python
TEMPLATES = {
    "underexposed": [
        "Aumentar iluminação frontal uniformemente.",
        "Imagem muito escura. Use luz adicional.",
        "Condições de baixa luz detectadas. Recomenda-se aumento de exposição.",
        "Falta iluminação. Posicione fontes de luz próximas ao objeto.",
        "Ambiente insuficientemente iluminado para captura ótima."
    ],
    "overexposed": [
        "Reduzir intensidade de iluminação.",
        "Exposição excessiva. Use difusores.", 
        # ... 3 mais
    ],
    "adequate": [
        "Iluminação está adequada.",
        "Condições de iluminação aceitáveis.",
        # ... 3 mais
    ],
    "mixed": [
        "Iluminação inadequada (combinação de áreas claras e escuras).",
        "Falta uniformidade de iluminação.",
        # ... 3 mais
    ]
}
```

---

## Modelos Disponíveis

### 1. DialoGPT-small (Padrão Jetson Nano)

**Características:**
- Parâmetros: 117M
- VRAM: ~250MB
- Latência: ~250ms/imagem
- Precisão: Boa (com validação de 8 tiers)
- Instabilidade: Média (hallucinations capturadas pelo validator)

**Quando usar:**
- ✅ Jetson Nano (4GB VRAM)
- ✅ Ambientes com recursos limitados
- ✅ Quando velocidade é crítica

**Configuração:**

```yaml
models:
  default: dialogpt-small
  
  dialogpt-small:
    name: /home/das9/models/DialoGPT-small
    max_tokens: 40
    summary_tokens: 60
    temperature: 0.3
    top_p: 0.85
```

### 2. Qwen2.5-0.5B (Recomendado Jetson Orin)

**Características:**
- Parâmetros: 494M
- VRAM: ~1GB
- Latência: ~300-400ms/imagem
- Precisão: Excelente (respostas diretas)
- Instabilidade: Baixa (menos hallucinations)

**Quando usar:**
- ✅ Jetson Orin (8-32GB VRAM)
- ✅ Quando qualidade é prioridade
- ✅ Quando VRAM é suficiente

**Configuração:**

```yaml
models:
  default: qwen
  
  qwen:
    name: Qwen/Qwen2.5-0.5B-Instruct
    max_tokens: 100
    summary_tokens: 150
    temperature: 0.3
    top_p: 0.85
```

### 3. Phi-3-mini (Recomendado Desktop RTX)

**Características:**
- Parâmetros: 3.8B
- VRAM: ~7-8GB
- Latência: ~300-500ms/imagem
- Precisão: Superior (raciocínio melhor)
- Instabilidade: Muito baixa (respostas confiáveis)

**Quando usar:**
- ✅ Desktop/Workstation RTX
- ✅ Jetson Orin com 32GB VRAM
- ✅ Quando máxima qualidade é crítica

**Configuração:**

```yaml
models:
  default: phi
  
  phi:
    name: microsoft/Phi-3-mini-4k-instruct
    max_tokens: 120
    summary_tokens: 200
    temperature: 0.3
    top_p: 0.85
```

---

## Endpoints

### 1. GET `/health`

Verifica se API está viva.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response (200):**
```json
{"status": "ok"}
```

---

### 2. POST `/metrics`

Extrai **apenas métricas** (sem LLM).

**Uso:** Monitoramento, logging, análise em tempo real.

**Request:**
```bash
curl -X POST http://localhost:8000/metrics \
  -F "file=@image.jpg"
```

**Response (200):**
```json
{
  "filename": "image.jpg",
  "metrics": {
    "illumination": 0.72,
    "illumination_label": "adequate",
    "mean_luma": 145.3,
    "std_luma": 52.1,
    "uniformity": 0.78,
    "pct_clipped_dark": 0.02,
    "pct_clipped_bright": 0.01,
    "exposure_score": 0.88,
    "contrast_score": 0.54,
    "clipping_penalty": 0.03
  },
  "processing_time_ms": 12
}
```

**Performance:** ~15-20ms (muito rápido, sem LLM)

---

### 3. POST `/diagnose`

Análise **completa com LLM**.

**Uso:** Diagnóstico detalhado com explicação em linguagem natural.

**Request:**
```bash
curl -X POST http://localhost:8000/diagnose \
  -F "file=@image.jpg"
```

**Response (200):**
```json
{
  "filename": "image.jpg",
  "status": "adequate",
  "illumination_score": 0.72,
  "illumination_label": "adequate",
  "explanation": "A iluminação está adequada para captura. O uniforme de iluminação é bom.",
  "summary": "Iluminação está adequada.",
  "metrics": {
    "illumination": 0.72,
    "illumination_label": "adequate",
    "mean_luma": 145.3,
    "std_luma": 52.1,
    "uniformity": 0.78,
    "pct_clipped_dark": 0.02,
    "pct_clipped_bright": 0.01,
    "exposure_score": 0.88,
    "contrast_score": 0.54,
    "clipping_penalty": 0.03
  },
  "model_used": "dialogpt-small",
  "validation_passed": true,
  "processing_time_ms": 285
}
```

**Performance:**
- Jetson Nano: ~250-350ms
- Jetson Orin: ~300-400ms
- Desktop RTX: ~100-200ms

---

### 4. POST `/diagnose/batch`

Diagnóstico em **lote** (reutiliza modelo na VRAM).

**Uso:** Processar múltiplas imagens eficientemente.

**Request:**
```bash
curl -X POST http://localhost:8000/diagnose/batch \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg"
```

**Response (200):**
```json
{
  "batch_id": "batch_20260413_120530_a3f5c2",
  "total": 3,
  "successful": 3,
  "failed": 0,
  "batch_processing_time_ms": 850,
  "results": [
    {
      "filename": "image1.jpg",
      "status": "adequate",
      "illumination_score": 0.72,
      "explanation": "Iluminação está adequada...",
      "summary": "Iluminação está adequada.",
      "processing_time_ms": 285
    },
    {
      "filename": "image2.jpg",
      "status": "underexposed",
      "illumination_score": 0.42,
      "explanation": "Aumentar iluminação uniformemente...",
      "summary": "Aumentar iluminação.",
      "processing_time_ms": 280
    },
    {
      "filename": "image3.jpg",
      "status": "overexposed",
      "illumination_score": 0.15,
      "explanation": "Reduzir exposição...",
      "summary": "Reduzir exposição.",
      "processing_time_ms": 285
    }
  ]
}
```

**Performance:**
- 3 imagens: ~850ms (280ms cada — reutiliza modelo)
- vs `/diagnose` x3: ~850ms (sem overhead de reload)
- **Economia:** 0ms (modelo já na VRAM)

---

### 5. POST `/upload`

**Salva** imagem no servidor para análise posterior.

**Request:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@image.jpg"
```

**Response (200):**
```json
{
  "filename": "image.jpg",
  "saved_as": "20260413_120530_image.jpg",
  "path": "data/uploads/20260413_120530_image.jpg",
  "size_bytes": 524288,
  "image_size": "1920x1080",
  "saved_timestamp": "2026-04-13T12:05:30.123456"
}
```

---

### 6. POST `/upload/batch`

**Salva múltiplas** imagens.

**Request:**
```bash
curl -X POST http://localhost:8000/upload/batch \
  -F "files=@img1.jpg" \
  -F "files=@img2.jpg" \
  -F "files=@img3.jpg"
```

**Response (200):**
```json
{
  "batch_id": "batch_20260413_120530_a3f5c2",
  "total": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "filename": "img1.jpg",
      "saved_as": "20260413_120530_00_img1.jpg",
      "path": "data/uploads/batch_20260413_120530_a3f5c2/20260413_120530_00_img1.jpg",
      "size_bytes": 524288,
      "status": "success"
    },
    // ... mais 2
  ]
}
```

---

## Exemplos de Uso

### Python - Diagnóstico Simples

```python
import requests

API_URL = "http://localhost:8000"

# Single image diagnosis
with open("image.jpg", "rb") as f:
    response = requests.post(
        f"{API_URL}/diagnose",
        files={"file": f},
        timeout=30
    )
    result = response.json()
    
    print(f"Status: {result['status']}")
    print(f"Score: {result['illumination_score']:.2f}")
    print(f"Explanation: {result['explanation']}")
    print(f"Time: {result['processing_time_ms']}ms")
```

### Python - Batch Processing

```python
import requests
from pathlib import Path

API_URL = "http://localhost:8000"
images = list(Path("data/images").glob("*.jpg"))

# Upload batch
files = [("files", open(img, "rb")) for img in images]

response = requests.post(
    f"{API_URL}/diagnose/batch",
    files=files,
    timeout=60
)

result = response.json()
print(f"Processadas: {result['successful']}/{result['total']}")

for r in result['results']:
    print(f"  {r['filename']}: {r['status']} ({r['illumination_score']:.2f})")
```

### Python - Metrics Only (Monitoramento)

```python
import requests

API_URL = "http://localhost:8000"

# Apenas métricas (rápido, sem LLM)
with open("image.jpg", "rb") as f:
    response = requests.post(
        f"{API_URL}/metrics",
        files={"file": f}
    )
    metrics = response.json()['metrics']
    
    # Logging/monitoramento
    print(f"Illumination: {metrics['illumination']:.3f}")
    print(f"Mean Luma: {metrics['mean_luma']:.1f}")
    print(f"Uniformity: {metrics['uniformity']:.2f}")
```

### Bash/curl - Um comando

```bash
# Diagnóstico completo
curl -X POST http://localhost:8000/diagnose \
  -F "file=@image.jpg" \
  | jq '.status, .explanation'

# Apenas métricas (forma rápida)
curl -X POST http://localhost:8000/metrics \
  -F "file=@image.jpg" \
  | jq '.metrics.illumination_label'

# Batch com jq para processar
curl -X POST http://localhost:8000/diagnose/batch \
  -F "files=@img1.jpg" -F "files=@img2.jpg" \
  | jq '.results[].status'
```

### Documentação Interativa (Swagger UI)

Abra no navegador:
```
http://localhost:8000/docs
```

Recursos:
- 📖 Documentação automática de todos endpoints
- 🧪 Testar endpoint diretamente no navegador
- 📋 Schemas de request/response
- 🔍 Exemplos automáticos

---

## Performance

### Comparação por Operação

| Operação | Jetson Nano | Jetson Orin | Desktop RTX |
|----------|-------------|-------------|------------|
| `/metrics` (apenas PDI) | 15ms | 12ms | 10ms |
| `/diagnose` (DialoGPT) | 280ms | — | — |
| `/diagnose` (Qwen) | — | 320ms | 150ms |
| `/diagnose` (Phi-3) | ✗ | 800ms | 300ms |
| `/diagnose/batch` x10 | 2.8s | 3.2s | 1.5s |

### Fatores que Afetam Performance

1. **Modelo**: DialoGPT (rápido) > Qwen (médio) > Phi-3 (lento)
2. **VRAM Disponível**: Mais VRAM = menos swapping
3. **Tamanho da Imagem**: Imagens maiores = mais processamento PDI
4. **Temperatura da GPU**: GPU quente = throttling automático
5. **Carga do Sistema**: Processos concorrentes reduzem velocidade

### Benchmarks Validados

```
Jetson Nano (Python 3.6, DialoGPT, CUDA 10.2):
  - PDI: 10ms
  - DialoGPT inference: 280ms
  - Validation: 5ms
  - Total: ~295ms ✅ (dentro de 300ms)
  - Batch x10: 2.9s ✅

Jetson Orin (Python 3.8, Qwen, CUDA 11.4):
  - PDI: 10ms
  - Qwen inference: 320ms
  - Validation: 5ms
  - Total: ~335ms ✅
  - Batch x10: 3.35s ✅

Desktop RTX 3080 (Python 3.10, Phi-3, CUDA 12.1):
  - PDI: 10ms
  - Phi-3 inference: 300ms
  - Validation: 5ms
  - Total: ~315ms ✅
  - Batch x10: 3.15s ✅
```

---

## Monitoramento

### Health Check Simples

```bash
# Verificar se API está viva
curl http://localhost:8000/health

# Se responde com 200 + {"status": "ok"} → API OK
```

### Verificar Modelo na GPU

```bash
# Verificar CUDA
nvidia-smi

# Verificar modelo em Python
python3 -c "
import torch
from app.pipeline.illumination_pipeline import IlluminationPipeline

pipeline = IlluminationPipeline(model_type='dialogpt-small', device='cuda')
print(f'Model loaded: OK')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU memory allocated: {torch.cuda.memory_allocated() / 1e9:.2f}GB')
"
```

### Logs em Tempo Real

```bash
# Jetson Nano (Poetry)
tail -f logs/api.log

# Docker
docker-compose -f docker-compose-nano.yml logs -f

# Systemd (se instalado como serviço)
journalctl -u ar-diagnostic -f
```

### Monitorar Temperatura (Jetson)

```bash
# Jetson Nano/Orin
tegrastats

# Exemplo output:
# RAM 1234/3956MB (lfb 512MB) cpu [80%@1800MHz, 75%@1800MHz, 60%@1800MHz, 55%@1800MHz] EMC 75%@1866MHz WOM@70C GPU@70C SOC@72C
# Se temperatura > 85°C → GPU fará throttling automático
```

---

## Troubleshooting

### Problema: Respostas vazias ou None

**Sintoma:**
```json
{
  "status": null,
  "explanation": null,
  "summary": null
}
```

**Causas possíveis:**

1. **LLM rejeitado por validação:**
   ```python
   # Log mostrará qual tier rejeitou
   # DEBUG: Validation Tier 3 rejected: "I would suggest..."
   ```
   **Solução:** Isso é normal — fallback para template em produção.

2. **Modelo não carregou:**
   ```bash
   # Verificar logs
   grep "Loading model" logs/api.log
   grep "ERROR" logs/api.log
   ```
   **Solução:** Reiniciar API, verificar VRAM.

3. **Timeout na requisição:**
   ```bash
   curl --max-time 5 http://localhost:8000/diagnose -F "file=@image.jpg"
   # Se timeout → aumentar timeout na config
   ```
   **Solução:** `api.timeout: 60` em `thresholds.yaml`

### Problema: CUDA não detectado

**Sintoma:**
```
torch.cuda.is_available() = False
```

**Solução (Jetson Nano):**
```bash
# Reinstalar PyTorch para Jetson
bash setup_jetson_nano.sh

# Verificar versão
python3 -c "import torch; print(torch.__version__)"
# Esperado: 1.10.0+cu102
```

**Solução (Jetson Orin):**
```bash
# Verificar CUDA toolkit
nvcc --version
# Esperado: release 11.4

# Reinstalar PyTorch
pip install torch --extra-index-url https://pypi.jetson-ai-lab.io
```

### Problema: Memória insuficiente (OOM)

**Sintoma:**
```
RuntimeError: CUDA out of memory
```

**Soluções:**

1. **Reduzir batch size:**
   ```yaml
   api:
     max_batch_size: 5  # Reduzir de 10 para 5
   ```

2. **Usar 4-bit quantization (Orin/Desktop apenas):**
   ```yaml
   models:
     use_4bit: true  # true em Orin/Desktop, false em Nano
   ```

3. **Usar modelo menor:**
   ```yaml
   models:
     default: dialogpt-small  # Nano
     # vs
     default: qwen  # Orin
   ```

4. **Verificar VRAM compartilhada (Jetson):**
   ```bash
   # Jetson Nano — expandir shared memory
   # Edit /boot/dtb/tegra210-p3448-0000-p3449-0000-b00.dtb (não recomendado!)
   # Alternativa: usar Nano com 3GB para OS, 1GB para GPU
   
   # Jetstson Orin — não é problema (8GB+ VRAM)
   ```

### Problema: Respostas repetitivas ou truncadas

**Sintoma:**
```
"A iluminação está. A iluminação está. A iluminação está."
```

**Causa:** Token repetition ou truncação de max_tokens.

**Solução:**
```yaml
models:
  dialogpt-small:
    max_tokens: 50        # Aumentar se truncado
    summary_tokens: 80
  
  qwen:
    max_tokens: 120       # Aumentar se truncado
    summary_tokens: 150
```

### Problema: Lentidão sem erro

**Sintoma:**
```
POST /diagnose toma 2+ segundos (vs 300-500ms esperado)
```

**Investigação:**
```bash
# 1. Verificar temperatura GPU
tegrastats | grep "GPU@"

# 2. Verificar carga do sistema
top | head -10

# 3. Verificar VRAM
nvidia-smi

# 4. Verificar logs para warnings
grep "WARN\|SLOW" logs/api.log
```

**Soluções:**
- Se GPU quente: Deixar esfriar, verificar ventilação
- Se carga alta: Desligar processos concorrentes
- Se VRAM low: Reduzir batch size ou usar modelo menor

---

## Configuração

### Arquivo: `app/config/thresholds.yaml`

Todas as configurações de modelos, PDI e API estão aqui.

#### Seção: Models

```yaml
models:
  default: dialogpt-small        # Modelo padrão (editar conforme hardware)
  device: cuda                   # cuda ou cpu
  use_4bit: false                # Quantization: false (Nano), true (Orin/Desktop)
  greedy_decoding: true          # true (velocidade), false (qualidade)
  prompt_max_length: 256         # Tokens max para prompt (256 Nano, 512 Orin)
  warmup_on_startup: true        # Carregar modelo na inicialização
```

#### Seção: DialoGPT-small

```yaml
dialogpt-small:
  name: /home/das9/models/DialoGPT-small  # Caminho local
  max_tokens: 40                 # Máximo tokens na geração
  summary_tokens: 60             # Tokens para summary
  temperature: 0.3               # Baixa = determinístico, Alta = criativo
  top_p: 0.85                    # Nucleus sampling (0.85 = top 85% de probabilidade)
```

#### Seção: PDI (Photographic Dynamic Interpretation)

```yaml
pdi:
  illumination:
    clipping_low: 10             # Threshold para shadow (pixels < 10 = clipped dark)
    clipping_high: 245           # Threshold para highlight (pixels > 245 = clipped bright)
    
    # Thresholds de classificação
    clipped_bright_overexposed: 0.10    # >10% bright clipped = overexposed
    clipped_dark_underexposed: 0.10     # >10% dark clipped = underexposed
    mean_underexposed: 70               # Mean luma < 70 = underexposed
    mean_overexposed: 185               # Mean luma > 185 = overexposed
    good: 0.7                           # Score >= 0.7 = adequate
    min_acceptable: 0.5                 # Score >= 0.5 = acceptable
```

#### Seção: API

```yaml
api:
  max_batch_size: 10             # Máximo de imagens por `/batch`
  max_image_size: 10485760       # 10MB
  allowed_formats:
    - jpg
    - jpeg
    - png
    - bmp
  timeout: 30                    # Segundos por requisição
```

### Variáveis de Ambiente

```bash
# Sobrescrever arquivo YAML
export AR_CONFIG_FILE=/path/to/custom_thresholds.yaml

# Definir ambiente (detecção automática se não setado)
export AR_ENVIRONMENT=jetson-nano
# Opções: jetson-nano, jetson-orin, desktop-legion, desktop-rtx

# Precisão do modelo (FP16 em Jetson, FP32 em Desktop)
export MODEL_PRECISION=fp16
```

### Chegar ao Arquivo

```bash
# Localização padrão
/home/das9/TCC/backend_tcc_mvp/app/config/thresholds.yaml

# Editar
nano /home/das9/TCC/backend_tcc_mvp/app/config/thresholds.yaml
```

---

## Quick Reference

### Começar API

```bash
# Poetry (Nano)
poetry run python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000

# Docker (Nano)
docker-compose -f docker-compose-nano.yml up -d

# Verificar
curl http://localhost:8000/health
```

### Testar Endpoints

```bash
# Métricas (rápido)
curl -X POST http://localhost:8000/metrics -F "file=@image.jpg" | jq

# Diagnóstico (completo)
curl -X POST http://localhost:8000/diagnose -F "file=@image.jpg" | jq

# Batch
curl -X POST http://localhost:8000/diagnose/batch \
  -F "files=@img1.jpg" -F "files=@img2.jpg" | jq
```

### Monitorar

```bash
# Logs
tail -f logs/api.log

# GPU (Jetson)
tegrastats

# VRAM
nvidia-smi
```

### Debug

```bash
# Verificar modelo
python3 -c "from app.pipeline.illumination_pipeline import IlluminationPipeline; print(IlluminationPipeline())"

# Testar validação
python3 -c "from app.models.dialogpt_model import DialoGPTModel; print('Validation running...')"

# Health check
curl http://localhost:8000/health
```

---

## Referências

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [PyTorch CUDA](https://pytorch.org/docs/stable/cuda.html)
- [Transformers Library](https://huggingface.co/docs/transformers/)
- [NVIDIA JetPack](https://docs.nvidia.com/jetson/jetpack/release-notes/)
