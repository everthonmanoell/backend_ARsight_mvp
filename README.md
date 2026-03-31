# AR Diagnostic MVP - Apenas Iluminação

**MVP pronto para produção para análise de iluminação de cenas AR em dispositivos Jetson.**

## 🎯 Escopo

Este é um **produto mínimo viável** focado exclusivamente em:
- ✅ Detecção de qualidade de iluminação (subexposta/adequada/superexposta)
- ✅ Aceleração GPU no Jetson Orin
- ✅ Modelos SLM Qwen 2.5 0.5B + Phi-3 Mini
- ✅ API REST com inferência em lote (batch)
- ✅ Fluxo de upload + diagnóstico em 2 etapas
- ✅ Integração com frontend Flutter mobile
- ❌ Sem detecção de pessoas YOLO
- ❌ Sem extração de ROI
- ❌ Sem métricas de oclusão/reflexos

## 📱 Frontend Flutter

Este backend foi desenvolvido para integrar com um **frontend Flutter mobile**.

**Fluxo no app:**
1. Usuário captura 10 imagens na câmera
2. App envia via `POST /upload/batch`
3. Recebe `batch_id` → mostra "✓ Imagens recebidas"
4. App solicita diagnóstico via `POST /diagnose/batch/{batch_id}`
5. Mostra "Processando diagnóstico..." enquanto aguarda
6. Recebe resultado completo com summary + métricas por frame
7. Exibe diagnóstico visual com risco geral e detalhes


## 🚀 Início Rápido

### Pré-requisitos

**Para Jetson Orin:**
- JetPack 6.0+
- CUDA 12.1+
- Python 3.10+
- Poetry

**Para Desktop (Legion/RTX):**
- Python 3.10+
- CUDA 12.1+ (para GPU)
- Poetry

### Instalação e Setup

#### 1️⃣ Jetson Orin

```bash
# Setup inicial (apenas uma vez!)
bash setup_jetson.sh

# Depois, toda vez que quiser rodar:
poetry run ar-api
```

**O que `setup_jetson.sh` faz:**
- ✅ Verifica versões de torch e accelerate
- ✅ Instala dependências Poetry
- ✅ Instala torch 2.8.0+cu126 do Jetson AI Lab
- ✅ Valida disponibilidade de CUDA

#### 2️⃣ Desktop Legion (x86_64 com RTX)

```bash
# Setup inicial (apenas uma vez!)
bash setup_legion.sh

# Depois, toda vez que quiser rodar:
poetry run ar-api
```

**O que `setup_legion.sh` faz:**
- ✅ Alterna para configuração Legion
- ✅ Reconstrói poetry.lock
- ✅ Instala todas as dependências (incluindo torch)
- ✅ Valida CUDA

### Acessar a API

**Localmente (localhost):**
```
http://localhost:8000
```

**Via hostname (Jetson):**
```
http://farmaciaback.local:8000
```

**Documentação Interativa (Swagger UI):**
```
http://localhost:8000/docs
```

ou

```
http://farmaciaback.local:8000/docs
```

**Para redirecionar porta via SSH (do seu desktop para a Jetson):**
```bash
ssh -L 8000:localhost:8000 farmaciaback@farmaciaback.local

# Depois acessa em: http://localhost:8000/docs
```

## 🔄 Fluxo de Diagnóstico em Batch (Upload + Processamento)

O novo fluxo separa o upload do diagnóstico em **2 etapas**, permitindo melhor controle e retry automático:

### Etapa 1️⃣ : Upload de Imagens

```bash
# Via localhost
curl -X POST http://localhost:8000/upload/batch \
  -F "files=@frame_1.jpg" \
  -F "files=@frame_2.jpg" \
  -F "files=@frame_3.jpg"

# Via Jetson hostname
curl -X POST http://farmaciaback.local:8000/upload/batch \
  -F "files=@frame_1.jpg" \
  -F "files=@frame_2.jpg" \
  -F "files=@frame_3.jpg"
```

**Resposta:**
```json
{
  "batch_id": "batch_20260331_150210_a1b2c3",
  "status": "uploaded",
  "files_saved": 3,
  "message": "Saved 3/3 files"
}
```

**Imagens salvas em:**
```
data/uploads/batch_20260331_150210_a1b2c3/
├── frame_00.jpg
├── frame_01.jpg
├── frame_02.jpg
├── metadata.json
└── status.json
```

### Etapa 2️⃣ : Iniciar Diagnóstico

```bash
curl -X POST http://localhost:8000/diagnose/batch/batch_20260331_150210_a1b2c3
```

**Resposta (síncrona):**
```json
{
  "batch_id": "batch_20260331_150210_a1b2c3",
  "status": "completed",
  "summary": {
    "overall_risk": "HIGH",
    "dominant_label": "overexposed",
    "normal_count": 2,
    "problem_count": 1,
    "explanation": "Imagens com iluminação inconsistente...",
    "recommendations": ["Ajustar ajuste de exposição..."],
    "metrics_avg": {
      "mean_brightness": 0.65,
      "mean_luma": 165.75,
      "uniformity": 0.87,
      "pct_clipped_dark": 0.0,
      "pct_clipped_bright": 0.05
    },
    "processing_time_s": 3.82
  },
  "frames": [
    {
      "frame_index": 0,
      "filename": "frame_00.jpg",
      "risk_level": "NORMAL",
      "status": "ok",
      "illumination_label": "adequate",
      "metrics": {
        "illumination_score": 0.92,
        "mean_brightness": 0.62,
        "uniformity": 0.89
      }
    },
    ...
  ]
}
```

### Alternativas: Consultar Status e Resultado (Polling)

```bash
# Consultar status
curl http://localhost:8000/diagnose/batch/batch_20260331_150210_a1b2c3/status

# Buscar resultado (se pronto)
curl http://localhost:8000/diagnose/batch/batch_20260331_150210_a1b2c3/result
```

## 💻 Teste Rápido Via Terminal

```bash
# Com imagens locais
python test_api_quick.py

# Ou com pasta de test customizada (edite BATCH_FOLDER no script)
poetry run python test_api_quick.py
```

## 📁 Estrutura do Projeto

```
backend_tcc_mvp/
├── app/
│   ├── api/
│   │   ├── main.py           # FastAPI app
│   │   └── routes.py         # Endpoints (/upload/batch, /diagnose/batch)
│   ├── config/
│   │   ├── config.py         # Carregador de config
│   │   └── thresholds.yaml   # Limites de classificação
│   ├── core/
│   │   ├── rule_engine.py    # Motor de regras
│   │   └── validators.py     # Validadores de métricas
│   ├── models/
│   │   ├── base_model.py
│   │   ├── qwen_model.py     # Qwen 2.5 0.5B
│   │   └── phi_model.py      # Phi-3 Mini
│   ├── pdi/
│   │   └── illumination.py   # Análise de iluminação (PDI)
│   ├── pipeline/
│   │   └── illumination_pipeline.py  # Pipeline orquestrador
│   └── utils/
│       └── templates.py       # Templates de prompts
├── data/
│   ├── illumination/
│   │   ├── bright_overexposed/
│   │   ├── dark_underexposed/
│   │   ├── normal/
│   │   └── uploads/          # Batches salvos
├── tests/
│   ├── test_api.py
│   └── manual/
└── docs/
    └── JETSON_DEPLOYMENT.md
```

## 🔧 Configuração

Editar `app/config/thresholds.yaml`:

```yaml
models:
  default: qwen  # ou 'phi'
  device: cuda   # ou 'cpu' ou 'auto'
  use_4bit: true # Habilitar para Jetson

pipeline:
  enabled_metrics:
    - illumination

rule_engine:
  illumination:
    underexposed_threshold: 0.35
    overexposed_threshold: 0.75
```

## 🐳 Implantação Docker (Jetson Nano)

```bash
# Construir para Jetson
docker build -f docker/Dockerfile.jetson-nano -t ar-diagnostic-mvp:jetson .

# Executar com GPU
docker run --gpus all -p 8000:8000 ar-diagnostic-mvp:jetson
```

Veja [docs/JETSON_DEPLOYMENT.md](docs/JETSON_DEPLOYMENT.md) para instruções detalhadas.

## 🧪 Testes

```bash
# Testar API com batch
python test_api_quick.py

# Executar testes completos
poetry run pytest
```

## 📊 Desempenho Esperado

| Ambiente | Modelo | Batch | Latência Total | VRAM |
|----------|--------|-------|-----------------|------|
| Jetson Orin | Qwen 0.5B | 10 imgs | ~3.8s | ~1.2GB |
| Desktop RTX | Qwen 0.5B | 10 imgs | ~2.8s | ~1.5GB |


## 🔄 Migração para Versão Completa

Quando o MVP for validado, integrar de volta ao `backend_tcc`:
1. Copiar `app/pdi/illumination.py` (otimizações)
2. Copiar `app/models/` (correções anti-alucinação)
3. Mesclar limiares de `app/config/thresholds.yaml`

## 📝 Licença

MIT

## 📈 Benchmark Jetson vs Legion

Para comparar automaticamente os resultados de performance entre `outputs/jetson` e `outputs/legion`:

```bash
python benchmark_jetson_vs_legion.py
```

Saídas geradas em `outputs/benchmark_comparison/`:
- `runs_raw.csv`: todas as execuções lidas dos JSONs
- `summary_by_env_model_batch.csv`: agregação por ambiente/modelo/batch
- `speedup_legion_vs_jetson.csv`: speedup comparável entre ambientes
- `benchmark_report.md`: relatório em Markdown
- `plots/*.png`: gráficos de latência e speedup

Se o ambiente não tiver matplotlib instalado, os CSVs e o relatório Markdown serão gerados normalmente, mas sem gráficos. Para habilitar os gráficos:

```bash
pip install matplotlib
```
