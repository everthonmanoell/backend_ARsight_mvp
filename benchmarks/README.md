# 📊 Benchmarks - Organização Centralizada

Tudo relacionado a benchmarking está aqui. Estrutura clara e fácil de navegar.

## 📁 Estrutura de Diretórios

```
benchmarks/
├── README.md                          # Este arquivo
├── BENCHMARKING_GUIDE.md              # Guia completo de como executar benchmarks
├── BENCHMARK_QUICK_REFERENCE.sh       # Comandos rápidos (copie e execute)
│
├── scripts/                           # Scripts Python para análise
│   ├── benchmark_jetson_vs_legion.py  # Comparação entre ambientes
│   ├── generate_comparison_report.py  # Gera relatório HTML/CSV
│   ├── analyze_perf.py                # Análise de performance
│   ├── compare_perf.py                # Comparação de métricas
│   └── check_*.py                     # Verificações rápidas
│
├── outputs/                           # Resultados dos benchmarks
│   ├── comparison/                    # Dados consolidados (últimos testes)
│   │   ├── runs_raw.csv               # Dados brutos
│   │   ├── summary_by_env_model_batch.csv
│   │   ├── speedup_vs_desktop_legion.csv
│   │   ├── benchmark_report.html      # Relatório visual
│   │   ├── benchmark_report.md        # Relatório em markdown
│   │   └── plots/                     # Gráficos PNG
│   │       ├── bar_*.png
│   │       ├── line_*.png
│   │       └── boxplot_*.png
│   │
│   └── legacy/                        # Histórico de testes antigos
│       ├── desktop-legion/batch{1-6}/
│       ├── jetson-nano/batch{1-6}/
│       └── jetson-orin/batch{1-6}/
│
├── data/                              # Dados de entrada para testes
│   └── images/                        # Imagens de teste (criar conforme necessário)
│
└── reports/                           # Relatórios para TCC
    ├── BENCHMARK_SUMMARY.md           # Resumo executivo
    ├── BENCHMARK_UPDATE.md            # Atualizações recentes
    └── CHANGELOG_BENCHMARKS.md        # Histórico de mudanças
```

---

## 🚀 Quick Start

### 1️⃣ Ver estrutura atual

```bash
cd benchmarks

# Ver tudo
tree -L 3

# Ver último relatório
cat outputs/comparison/benchmark_report.md

# Ver gráficos
ls outputs/comparison/plots/

# Ver dados brutos
head outputs/comparison/summary_by_env_model_batch.csv
```

### 2️⃣ Executar novo benchmark

```bash
# Verificar guia completo
cat BENCHMARKING_GUIDE.md

# Usar quick reference
bash BENCHMARK_QUICK_REFERENCE.sh

# Ou executar script individual
cd scripts
python benchmark_jetson_vs_legion.py --help
```

### 3️⃣ Gerar gráficos

```bash
cd scripts
python generate_comparison_report.py \
  --input-dir ../outputs/comparison/ \
  --output-dir ../outputs/comparison/
```

---

## 📋 Arquivos Principais

### `BENCHMARKING_GUIDE.md`
- **O quê:** Guia detalhado para executar benchmarks
- **Quando ler:** Antes de rodar novos testes
- **Seções:** Estrutura proposta, métricas, scripts, gráficos recomendados

### `BENCHMARK_QUICK_REFERENCE.sh`
- **O quê:** Comandos prontos para copiar
- **Quando usar:** Quando quer executar rápido
- **Fases:** Setup → Testes Primários → Relatórios → Consolidação

### `scripts/`
- **benchmark_jetson_vs_legion.py** - Comparação principal
- **generate_comparison_report.py** - Gerador de relatórios
- **analyze_perf.py** - Extração de métricas
- **check_*.py** - Verificações rápidas

### `outputs/`
- **comparison/** - Dados + gráficos do(s) último(s) teste(s)
- **legacy/** - Histórico completo (para referência histórica)

### `reports/`
- Documentos formatados para incluir no TCC

---

## 📊 Últimos Resultados

Se há dados em `outputs/comparison/`:

```bash
# Ver resumo
cat outputs/comparison/benchmark_report.md

# Ver speedup
cat outputs/comparison/speedup_vs_desktop_legion.csv

# Gráficos
ls -lh outputs/comparison/plots/
```

---

## 🔄 Fluxo de Trabalho Típico

### Fase 1: Preparar
```bash
cd benchmarks
mkdir -p outputs/comparison/plots
```

### Fase 2: Executar Testes
```bash
# Em cada ambiente (Nano, Orin, RTX)
python scripts/benchmark_jetson_vs_legion.py \
  --model <dialogpt|qwen|phi> \
  --env <jetson-nano|jetson-orin|desktop-rtx>
```

### Fase 3: Analisar
```bash
python scripts/generate_comparison_report.py \
  --input-dir outputs/comparison/
```

### Fase 4: Visualizar
```bash
# Abrir em navegador
open outputs/comparison/benchmark_report.html

# Ou ler em terminal
cat outputs/comparison/benchmark_report.md
```

---

## 💾 Dados Capturados

Cada benchmark salva:

```json
{
  "environment": "jetson-nano",
  "model": "dialogpt-small",
  "batch": "batch1",
  "timing": {
    "pdi_per_image_ms": 12.5,
    "llm_per_diag_ms": 280.3,
    "total_per_image_ms": 292.8
  },
  "performance": {
    "throughput_imgs_per_sec": 3.42,
    "target_met": true
  },
  "quality": {
    "accuracy": 100.0,
    "validation_rate": 100.0
  }
}
```

---

## 📈 Gráficos Disponíveis

Em `outputs/comparison/plots/`:

- `bar_slm_per_diag_mean.png` - LLM latency por ambiente
- `bar_speedup_vs_legion.png` - Speedup vs Desktop
- `boxplot_total_s_by_environment.png` - Distribuição de latência
- `line_total_s_mean_by_batch.png` - Tendência ao longo dos batches

---

## 🎯 Próximas Ações

### Para Testes Novos
1. Criar `data/images/batch_X/` com novas imagens
2. Executar benchmarks (ver QUICK_REFERENCE.sh)
3. Gerar relatório (generate_comparison_report.py)
4. Mover arquivos para `outputs/comparison/`

### Para TCC
1. Copiar gráficos de `outputs/comparison/plots/` para tese
2. Usar dados em `outputs/comparison/*.csv` para tabelas
3. Referenciar `reports/` para contexto

### Limpeza
```bash
# Mover resultados antigos para legacy
mv outputs/comparison/* outputs/legacy/
mkdir outputs/comparison/plots

# Ou remover tudo
rm -rf outputs/comparison/*
```

---

## 📚 Referências Rápidas

| Tarefa | Arquivo |
|--------|---------|
| Entender como rodar testes | `BENCHMARKING_GUIDE.md` |
| Copiar comandos prontos | `BENCHMARK_QUICK_REFERENCE.sh` |
| Analisar dados de plots | `scripts/generate_comparison_report.py` |
| Ver último relatório | `outputs/comparison/benchmark_report.md` |
| Histórico completo | `outputs/legacy/` |

---

## 🔍 Troubleshooting

### "Não encontro os últimos resultados"
```bash
# Ver o que tem em outputs/
ls -la outputs/comparison/
ls -la outputs/legacy/
```

### "Quero rodar rapidinho um teste"
```bash
bash BENCHMARK_QUICK_REFERENCE.sh
```

### "Preciso dos dados em CSV"
```bash
ls outputs/comparison/*.csv
cat outputs/comparison/summary_by_env_model_batch.csv
```

---

**Última atualização:** 2026-04-13  
**Estrutura versão:** 2.0 (Centralizada)
