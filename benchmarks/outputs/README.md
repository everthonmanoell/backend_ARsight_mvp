# Resultados de Benchmarks

Dados e gráficos dos testes de performance.

## 📁 Estrutura

```
outputs/
├── comparison/           ← Últimos testes (dados + gráficos)
└── legacy/              ← Histórico antigo (para referência)
```

---

## 📊 comparison/ (Último(s) Teste(s))

Aqui ficam os resultados mais recentes.

### Arquivos CSV

- **runs_raw.csv** - Dados brutos de cada execução
- **summary_by_env_model_batch.csv** - Resumo por ambiente/modelo/batch
- **speedup_vs_desktop_legion.csv** - Comparação de velocidade

### Relatórios

- **benchmark_report.html** - Visualização interativa (abrir no navegador)
- **benchmark_report.md** - Versão em texto (ler no terminal)

### plots/ (Gráficos)

Arquivo PNG para cada tipo de gráfico:
- `bar_*.png` - Gráficos de barras
- `line_*.png` - Gráficos de linha
- `boxplot_*.png` - Distribuições

**Usar em:** Apresentações, TCC, relatórios

---

## 🗂️ legacy/ (Histórico)

Dados antigos organizados por ambiente.

```
legacy/
├── desktop-legion/
│   ├── batch1/
│   ├── batch2/
│   └── ...
├── jetson-nano/
│   ├── batch1/
│   ├── batch2/
│   └── ...
└── jetson-orin/
    ├── batch1/
    ├── batch2/
    └── ...
```

**Quando usar:**
- Comparar teste antigo vs. novo
- Analisar tendências históricas
- Referência de baseline

---

## 🔄 Como Atualizar Dados

### Quando você roda novo benchmark:

1. **Novos testes geram novos CSVs**
   ```bash
   python scripts/benchmark_jetson_vs_legion.py
   # → Cria outputs/comparison/*.csv
   ```

2. **Gerar novo relatório**
   ```bash
   python scripts/generate_comparison_report.py
   # → Cria outputs/comparison/benchmark_report.html
   # → Cria outputs/comparison/plots/*.png
   ```

3. **Mover antigos para legacy (opcional)**
   ```bash
   mv outputs/comparison/* outputs/legacy/
   ```

---

## 📈 Visualizar Dados

### Ver última comparação

```bash
# HTML interativo
open comparison/benchmark_report.html

# Texto
cat comparison/benchmark_report.md

# CSV
cat comparison/summary_by_env_model_batch.csv
```

### Ver histórico

```bash
# Qual era o performance do Nano na batch1?
ls legacy/jetson-nano/batch1/

# Comparar speedup antigo vs. novo
diff legacy/speedup* comparison/speedup*
```

---

## 💾 Formato dos Dados

### CSV típico (summary_by_env_model_batch.csv)

```
environment,model,batch,runs,total_s_mean,slm_per_diag_mean,...
jetson-nano,qwen,batch1,14,148.736,14.774,...
desktop-legion,phi,batch1,5,6.911,0.672,...
```

### JSON raw (runs_raw.csv)

Cada linha é um teste completo com:
- Timestamps
- Timings (PDI, LLM, total)
- Performance (throughput, target_met)
- Quality (accuracy, validation_rate)

---

## 🗑️ Limpeza

### Remover tudo e começar do zero

```bash
rm -rf comparison/*
rm -rf legacy/*
mkdir comparison/plots
```

### Fazer backup de dados antigos

```bash
tar -czf outputs_backup_$(date +%Y%m%d).tar.gz legacy/
mv outputs_backup_*.tar.gz ~/backups/
```

---

## 📍 Próximos Passos

- [ ] Entender os dados em `comparison/`
- [ ] Abrir `benchmark_report.html` para visualizar
- [ ] Analisar `speedup_vs_desktop_legion.csv`
- [ ] Usar gráficos em `plots/` para TCC

---

**Última atualização:** 2026-04-13
