# Comparação - Último(s) Teste(s)

Dados e gráficos dos testes mais recentes.

## 📊 Arquivos

### CSVs (Dados)

**runs_raw.csv** (grande)
- Dados brutos de cada execução
- Uma linha por teste completo
- Inclui: timings, performance, quality, environment

**summary_by_env_model_batch.csv**
- Resumo de cada combinação (env + modelo + batch)
- Agregações e médias
- Melhor para análise rápida

**speedup_vs_desktop_legion.csv**
- Comparação de velocidade
- Speedup ratio (Orin/RTX vs Legion)
- Útil para TCC

### Relatórios (Visualização)

**benchmark_report.html**
- Versão interativa (abrir no navegador)
- Tabelas formatadas
- Recomendado para visualizar

**benchmark_report.md**
- Versão em texto/markdown
- Pode ser incluída em TCC
- `cat` no terminal

### Gráficos (plots/)

**bar_slm_per_diag_mean.png**
- LLM latency por modelo/env

**bar_speedup_vs_legion.png**
- Speedup em relação ao Desktop

**boxplot_total_s_by_environment.png**
- Distribuição de latência

**line_total_s_mean_by_batch.png**
- Tendência ao longo dos batches

---

## 🚀 Como Usar

### Ver última comparação

```bash
# Abrir em navegador
open benchmark_report.html

# Ou ler no terminal
cat benchmark_report.md
```

### Extrair dados específicos

```bash
# Quantas linhas de dados?
wc -l runs_raw.csv

# Performance do Nano?
grep "jetson-nano" summary_by_env_model_batch.csv

# Speedup do Orin?
cat speedup_vs_desktop_legion.csv
```

### Incluir em apresentação

```bash
# Copiar gráficos para slides/TCC
cp plots/*.png ~/meu-tcc/imagens/
```

---

## 📈 Interpretação dos Dados

### summary_by_env_model_batch.csv

Colunas principais:
- `environment`: jetson-nano, jetson-orin, desktop-legion
- `model`: dialogpt-small, qwen, phi
- `batch`: batch1, batch2, batch3
- `total_s_mean`: Tempo total MÉDIO (segundos)
- `slm_per_diag_mean`: Latência LLM (ms)
- `accuracy_mean`: Taxa de acerto (%)
- `target_met_rate`: % que atendeu <300ms

Exemplo de leitura:
```
jetson-nano, dialogpt-small, batch1:
- 2.93s por 10 imagens
- DialoGPT levou 280ms
- 100% acurácia
- Todos os 10 atenderam target
```

### speedup_vs_desktop_legion.csv

```
model, batch, speedup_slm, speedup_total

Exemplo:
qwen, batch1, 0.985, 0.986

Leitura: Orin é 1% mais LENTO que Desktop (não é speedup real)
         Motivo: Desktop RTX é mais rápido que Orin
```

---

## 🔄 Atualizar Dados

### Quando você roda novo benchmark:

```bash
# Na raiz do projeto
cd ..

# Executar novo teste
python scripts/benchmark_jetson_vs_legion.py

# Gerar novo relatório
python scripts/generate_comparison_report.py \
  --input-dir outputs/comparison/

# Voltar
cd outputs/comparison/
```

### Arquivo novo é gerado? Sim!

```bash
# Antigos arquivos são sobrescritos
ls -la *.csv
```

---

## 🗂️ Histórico

Se quer manter histórico:

```bash
# Backup antes de rodar novo teste
cp *.csv ../legacy/old_run_$(date +%Y%m%d)/

# Depois roda novo teste
# Gera novos CSVs
```

---

## 📍 Referência

Ver estrutura completa em: `../README.md`

---

**Última atualização:** 2026-04-13
