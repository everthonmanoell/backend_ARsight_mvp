# Test New Endpoints

Exemplos de uso dos novos endpoints do MVP.

## 1. Extract Metrics Only (sem LLM - mais rápido)

```bash
# Windows PowerShell
curl.exe -X POST http://localhost:8000/metrics -F "file=@data/illumination/adequate/normal_image1.jpg"
```

**Response:**
```json
{
  "filename": "normal_image1.jpg",
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
  }
}
```

**Vantagens:**
- ⚡ ~100x mais rápido (sem LLM)
- 📊 Ideal para logging/monitoramento
- 🔢 Apenas números, sem explicação

---

## 2. Upload Single Image

```bash
# Salva imagem no servidor
curl.exe -X POST http://localhost:8000/upload -F "file=@data/illumination/adequate/normal_image1.jpg"
```

**Response:**
```json
{
  "filename": "normal_image1.jpg",
  "saved_as": "20260227_210530_normal_image1.jpg",
  "path": "data/uploads/20260227_210530_normal_image1.jpg",
  "size_bytes": 524288,
  "image_size": "1920x1080"
}
```

**Use case:**
- 💾 Armazena imagens para análise posterior
- 📁 Cria dataset de imagens problemáticas
- 🔍 Debug de casos específicos

---

## 3. Upload Batch

```bash
# Salva múltiplas imagens
curl.exe -X POST http://localhost:8000/upload/batch ^
  -F "files=@data/illumination/underexposed/dark_image1.jpg" ^
  -F "files=@data/illumination/adequate/normal_image1.jpg" ^
  -F "files=@data/illumination/overexposed/bright_image1.jpg"
```

**Response:**
```json
{
  "total": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "filename": "dark_image1.jpg",
      "saved_as": "20260227_210530_00_dark_image1.jpg",
      "path": "data/uploads/20260227_210530_00_dark_image1.jpg",
      "size_bytes": 412345,
      "image_size": "1920x1080",
      "status": "success"
    },
    ...
  ]
}
```

---

## 4. Interactive Documentation (Swagger)

Abra no navegador:
```
http://localhost:8000/docs
```

**Features:**
- 📖 Documentação interativa completa
- 🧪 Teste endpoints diretamente no navegador
- 📋 Schemas de request/response
- 🔍 Exemplos automáticos

---

## 📊 Comparação de Endpoints

| Endpoint | LLM | Salva | Velocidade | Use Case |
|----------|-----|-------|------------|----------|
| `/diagnose` | ✅ | ❌ | Lento (~1.2s) | Diagnóstico completo com explicação |
| `/diagnose/batch` | ✅ | ❌ | Lento | Diagnóstico em lote |
| `/metrics` | ❌ | ❌ | Rápido (~0.01s) | Monitoramento, logging, análise |
| `/upload` | ❌ | ✅ | Rápido | Salvar imagens problemáticas |
| `/upload/batch` | ❌ | ✅ | Rápido | Criar dataset |

---

## 🔄 Workflows Comuns

### Workflow 1: Diagnóstico Completo
```bash
# 1. Upload image
curl.exe -X POST http://localhost:8000/upload -F "file=@image.jpg"

# 2. Diagnose
curl.exe -X POST http://localhost:8000/diagnose -F "file=@image.jpg"
```

### Workflow 2: Monitoramento Rápido
```bash
# Apenas métricas (sem LLM)
curl.exe -X POST http://localhost:8000/metrics -F "file=@image.jpg"
```

### Workflow 3: Coleta de Dataset
```bash
# Upload batch para criar dataset
curl.exe -X POST http://localhost:8000/upload/batch -F "files=@img1.jpg" -F "files=@img2.jpg"
```

---

## 🧪 Python Example

```python
import requests

# API base URL
API_URL = "http://localhost:8000"

# 1. Extract metrics only (fast)
with open("image.jpg", "rb") as f:
    response = requests.post(f"{API_URL}/metrics", files={"file": f})
    metrics = response.json()
    print(f"Illumination: {metrics['metrics']['illumination']:.2f}")

# 2. Full diagnosis (slow, with LLM)
with open("image.jpg", "rb") as f:
    response = requests.post(f"{API_URL}/diagnose", files={"file": f})
    result = response.json()
    print(f"Status: {result['status']}")
    print(f"Explanation: {result['explanation']}")

# 3. Upload and save
with open("image.jpg", "rb") as f:
    response = requests.post(f"{API_URL}/upload", files={"file": f})
    saved = response.json()
    print(f"Saved as: {saved['saved_as']}")
```

---

## ⚡ Performance Tips

1. **Use `/metrics` para monitoramento em tempo real** (~100x mais rápido)
2. **Use `/diagnose/batch` em vez de múltiplos `/diagnose`** (reutiliza modelo)
3. **Upload imagens primeiro, processe depois** (melhor para pipelines)
4. **Cache resultados de métricas** (iluminação não muda frequentemente)
