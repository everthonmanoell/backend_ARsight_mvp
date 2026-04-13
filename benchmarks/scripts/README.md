# Scripts de Análise e Benchmark

Todos os scripts Python para análise de performance e geração de relatórios.

## 📋 Scripts Disponíveis

### benchmark_jetson_vs_legion.py
**O que faz:** Script principal de benchmarking
- Compara desempenho entre Jetson Nano, Jetson Orin e Desktop Legion
- Executa testes e coleta métricas
- Gera CSV com dados brutos

**Como usar:**
```bash
python benchmark_jetson_vs_legion.py \
  --desktop-legion-dir ../outputs/comparison \
  --jetson-nano-dir ../outputs/legacy/jetson-nano \
  --jetson-orin-dir ../outputs/legacy/jetson-orin \
  --out-dir ../outputs/comparison
```

**Saída:** `runs_raw.csv`, `summary_by_env_model_batch.csv`

---

### generate_comparison_report.py
**O que faz:** Gera relatórios e gráficos
- Lê dados de CSV
- Gera HTML interativo
- Cria PNG com plots

**Como usar:**
```bash
python generate_comparison_report.py \
  --input-dir ../outputs/comparison/ \
  --output-dir ../outputs/comparison/
```

**Saída:** `benchmark_report.html`, `.md`, `/plots/*.png`

---

### analyze_perf.py
**O que faz:** Extrai e analisa métricas
- Calcula latência média
- Throughput
- Taxa de sucesso

**Como usar:**
```bash
python analyze_perf.py ../outputs/comparison/runs_raw.csv
```

---

### compare_perf.py
**O que faz:** Compara dois conjuntos de teste
- Vê mudanças de performance
- Identifica regressões

**Como usar:**
```bash
python compare_perf.py \
  ../outputs/legacy/jetson-nano/run1.csv \
  ../outputs/comparison/latest.csv
```

---

### check_*.py
**O que medem:** Verificações rápidas

- `check_baseline.py` - Baseline de performance esperado
- `check_config.py` - Configuração do ambiente
- `check_final.py` - Teste final após mudanças
- `check_latest.py` - Resultado do último teste

**Como usar:**
```bash
python check_latest.py
```

---

## 🔧 Como Adicionar Novo Script

1. Criar arquivo `.py` nesta pasta
2. Adicionar `#!/usr/bin/env python3` no topo
3. Documentar no `README.md` desta pasta
4. Testar localmente:
   ```bash
   python seu_novo_script.py --help
   ```

---

## 📊 Fluxo de Execução Típico

```
1. Executar teste
   python benchmark_jetson_vs_legion.py
   ↓
2. Gerar relatório
   python generate_comparison_report.py
   ↓
3. Analisar dados
   python analyze_perf.py
   ↓
4. Visualizar em navegador
   open ../outputs/comparison/benchmark_report.html
```

---

## 🐛 Troubleshooting Scripts

**"ModuleNotFoundError: No module named 'XXX'"**
```bash
# Voltar para raiz do projeto
cd ../../
python -m pip install -r requirements.txt
```

**"FileNotFoundError: [Errno 2] No such file or directory"**
```bash
# Verificar caminhos - scripts esperam rodar de /benchmarks/scripts/
pwd  # deve ser /benchmarks/scripts/
ls ../outputs/comparison/  # verificar arquivos
```

**"Permission denied"**
```bash
chmod +x seu_script.py
```
