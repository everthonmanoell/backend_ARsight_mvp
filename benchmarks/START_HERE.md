# 🚀 START HERE - Navegação Rápida

Bem-vindo à pasta centralizada de benchmarks!

## 👉 Comece Por Aqui

```
Primeira vez? Leia isto em ordem:

1. Este arquivo (START_HERE.md) ← Você está aqui
2. README.md ← Visão geral
3. INDEX.txt ← Mapa de estrutura
4. BENCHMARK_QUICK_REFERENCE.sh ← Comandos prontos
5. BENCHMARKING_GUIDE.md ← Entender tudo
```

---

## 🗺️ Mapa Rápido

### 📖 Documentação

| Arquivo | Conteúdo | Quando Ler |
|---------|----------|-----------|
| **README.md** | Visão geral + estrutura | Primeira vez |
| **INDEX.txt** | Índice visual | Perdido? Leia isto |
| **BENCHMARKING_GUIDE.md** | Guia completo | Antes de rodar testes |
| **BENCHMARK_QUICK_REFERENCE.sh** | Comandos prontos | Quer executar logo |

### 🔧 Scripts

| Arquivo | O que faz |
|---------|-----------|
| `scripts/benchmark_jetson_vs_legion.py` | Script principal de testes |
| `scripts/generate_comparison_report.py` | Gera relatórios + gráficos |
| `scripts/analyze_perf.py` | Analisa métricas |

### 📊 Dados

| Pasta | Conteúdo |
|-------|----------|
| `outputs/comparison/` | **Últimos testes** (dados + gráficos) |
| `outputs/legacy/` | Histórico antigo |
| `reports/` | Documentos formatados para TCC |
| `data/` | Imagens para testes |

---

## ⚡ 3 Minutos de Setup

```bash
# 1. Ver estrutura
cat README.md

# 2. Ver índice
cat INDEX.txt

# 3. Um comando test
bash BENCHMARK_QUICK_REFERENCE.sh

# Pronto! 🎉
```

---

## 🎯 Casos de Uso

### "Quero ver o último benchmark"
```bash
cat outputs/comparison/benchmark_report.md
# ou
open outputs/comparison/benchmark_report.html
```

### "Quero rodar novo teste"
```bash
# Ler guia
cat BENCHMARKING_GUIDE.md

# Usar quick reference
bash BENCHMARK_QUICK_REFERENCE.sh
```

### "Preciso de gráficos para TCC"
```bash
ls outputs/comparison/plots/
# Copie os PNG para seu trabalho
```

### "Quero entender a estrutura"
```bash
cat INDEX.txt
# ou
tree -L 2 .
```

### "Estou perdido"
```bash
cat README.md
# Depois
cat INDEX.txt
```

---

## 📚 Documentação Completa (Em Ordem)

1. **START_HERE.md** (este arquivo)
   - Quick reference para navegação
   
2. **README.md**
   - Visão geral + estrutura
   - Quick start
   - Troubleshooting
   
3. **INDEX.txt**
   - Índice visual de todas as pastas
   - Dicas e referências
   
4. **BENCHMARKING_GUIDE.md**
   - Guia completo de benchmarking
   - Matriz de testes recomendada
   - Como executar
   - Métricas
   - Gráficos para TCC
   
5. **BENCHMARK_QUICK_REFERENCE.sh**
   - Comandos prontos
   - Fases: Setup → Testes → Relatórios
   - Copie, cole, execute

6. **Subpastas/README.md**
   - `scripts/README.md` - Documentação dos scripts
   - `outputs/README.md` - Explicação de dados
   - `outputs/comparison/README.md` - Último teste
   - `outputs/legacy/README.md` - Histórico
   - `reports/README.md` - Para TCC
   - `data/README.md` - Dados de entrada

---

## 🎓 Para TCC

```markdown
# Usando Benchmarks no TCC

1. Copiar dados de:
   benchmarks/outputs/comparison/summary_by_env_model_batch.csv

2. Copiar gráficos de:
   benchmarks/outputs/comparison/plots/*.png

3. Referenciar metodologia de:
   benchmarks/BENCHMARKING_GUIDE.md

4. Usar tabelas formatadas de:
   benchmarks/reports/BENCHMARK_SUMMARY.md
```

---

## 💡 Dicas Rápidas

- 🗂️ Tudo está aqui em `benchmarks/` → fácil de encontrar
- 📖 Cada subpasta tem `README.md` → leia antes
- 🚀 `BENCHMARK_QUICK_REFERENCE.sh` → comandos prontos
- 📊 `outputs/comparison/` → últimos dados + gráficos
- 🗑️ `outputs/legacy/` → histórico (para referência)

---

## 🔗 Próximos Passos

Escolha um:

### Quick Path (5 min)
```
START_HERE.md → README.md → bash BENCHMARK_QUICK_REFERENCE.sh
```

### Full Understanding (30 min)
```
START_HERE.md → README.md → BENCHMARKING_GUIDE.md → scripts/README.md
```

### Just the Data (2 min)
```
outputs/comparison/ → abrir benchmark_report.html
```

---

## ❓ FAQ Rápido

**P: Onde vejo o último resultado?**  
R: `cat outputs/comparison/benchmark_report.md` ou `open outputs/comparison/benchmark_report.html`

**P: Como rodo novo teste?**  
R: `bash BENCHMARK_QUICK_REFERENCE.sh` ou `cat BENCHMARKING_GUIDE.md`

**P: Onde estão os gráficos?**  
R: `outputs/comparison/plots/`

**P: Como uso para TCC?**  
R: `cat reports/README.md`

**P: Estou confuso!**  
R: `cat INDEX.txt` - índice visual de tudo

---

## 🎯 Seu Próximo Clique

```
👇 Escolha um:

1️⃣  Entender a estrutura
   → cat README.md

2️⃣  Ver último benchmark
   → open outputs/comparison/benchmark_report.html

3️⃣  Rodarmeu próprio teste
   → bash BENCHMARK_QUICK_REFERENCE.sh

4️⃣  Usar para TCC
   → cat reports/README.md

5️⃣  Ver índice de tudo
   → cat INDEX.txt
```

---

**Boa sorte! 🚀**

*Última atualização: 2026-04-13*
