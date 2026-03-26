# AR Diagnostic MVP - Apenas Iluminação

**MVP pronto para produção para análise de iluminação de cenas AR em dispositivos Jetson.**

## 🎯 Escopo

Este é um **produto mínimo viável** focado exclusivamente em:
- ✅ Detecção de qualidade de iluminação (subexposta/adequada/superexposta)
- ✅ Aceleração GPU no Jetson
- ✅ Modelos SLM Qwen 2.5 0.5B + Phi-3 Mini
- ✅ API REST com inferência única e em lote
- ❌ Sem detecção de pessoas YOLO
- ❌ Sem extração de ROI
- ❌ Sem métricas de oclusão/reflexos

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.10+
- CUDA 12.1+ (para aceleração GPU)
- Poetry (recomendado) ou pip

### Instalação

**Com Poetry (recomendado):**
```bash
poetry install
poetry run ar-api
```

**Com pip:**
```bash
pip install -r requirements.txt
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

### Testar a API

```bash
# Verificação de saúde
curl http://localhost:8000/health

# Diagnóstico de imagem única (com explicação LLM)
curl -X POST http://localhost:8000/diagnose \
  -F "file=@data/illumination/underexposed/dark_image1.jpg"

# Extrair apenas métricas (rápido, sem LLM)
curl -X POST http://localhost:8000/metrics \
  -F "file=@data/illumination/underexposed/dark_image1.jpg"

# Fazer upload e salvar imagem
curl -X POST http://localhost:8000/upload \
  -F "file=@data/illumination/underexposed/dark_image1.jpg"

# Diagnóstico em lote
curl -X POST http://localhost:8000/diagnose/batch \
  -F "files=@data/illumination/underexposed/dark_image1.jpg" \
  -F "files=@data/illumination/adequate/normal_image1.jpg"

# Documentação interativa (Swagger)
# Abrir no navegador: http://localhost:8000/docs
```

## 📁 Estrutura do Projeto

```
backend_tcc_mvp/
├── app/
│   ├── api/           # Rotas FastAPI
│   ├── config/        # Configuração YAML
│   ├── core/          # Motor de regras & validadores
│   ├── models/        # Modelos SLM Qwen & Phi
│   ├── pdi/           # Analisador PDI de iluminação
│   └── utils/         # Templates
├── data/
│   └── illumination/  # Imagens de teste
├── tests/             # Testes unitários & de integração
├── docker/            # Dockerfile.jetson
└── docs/              # Guias de implantação
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

## 🐳 Implantação Docker (Jetson)

```bash
# Construir para Jetson
docker build -f docker/Dockerfile.jetson -t ar-diagnostic-mvp:jetson .

# Executar com GPU
docker run --gpus all -p 8000:8000 ar-diagnostic-mvp:jetson
```

Veja [docs/JETSON_DEPLOYMENT.md](docs/JETSON_DEPLOYMENT.md) para instruções detalhadas.

## 🧪 Testes

```bash
# Executar todos os testes
poetry run pytest

# Testar iluminação manualmente
python tests/test_illumination_batch.py
```

## 📊 Desempenho (Jetson Xavier NX)

| Modelo | Quantização | Latência | VRAM |
|--------|-------------|----------|------|
| Qwen 0.5B | 4-bit | ~1.2s | ~800MB |
| Phi-3 Mini | 4-bit | ~1.8s | ~1.2GB |

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
