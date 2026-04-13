# Relatórios para TCC

Documentação formatada para incluir na tese/apresentação.

## 📄 Arquivos

### BENCHMARK_SUMMARY.md
Resumo executivo dos resultados principais:
- Performance por ambiente
- Tabelas de comparação
- Conclusões

**Use em:** Introdução do capítulo de benchmarks

### BENCHMARK_UPDATE.md
Atualizações mais recentes:
- Mudanças de performance
- Otimizações aplicadas
- Problemas resolvidos

**Use em:** Changelog ou histórico

### CHANGELOG_BENCHMARKS.md
Histórico completo de todas as mudanças

**Use em:** Apêndice ou referência histórica

---

## 🎓 Como Usar para TCC

### 1. Incluir Tabelas

Copie tabelas de:
```markdown
benchmarks/outputs/comparison/benchmark_report.md
```

Cole em sua tese:
```markdown
## Resultados de Performance

[Tabela copiada de BENCHMARK_SUMMARY.md]
```

### 2. Incluir Gráficos

Copie PNGs de:
```
benchmarks/outputs/comparison/plots/
```

Para seu projeto LaTeX/Word/Markdown:
```markdown
![Latência por Ambiente](../benchmarks/outputs/comparison/plots/line_*.png)
```

### 3. Referenciar em Roadmap

```markdown
## Metodologia Experimental

Ver detalhes em: `benchmarks/BENCHMARKING_GUIDE.md`

### Métricas Coletadas

[Listar métricas de BENCHMARKING_GUIDE.md]
```

---

## 📝 Template para Seção TCC

```markdown
## Capítulo X: Avaliação de Performance

### X.1 Metodologia

[Referência: benchmarks/BENCHMARKING_GUIDE.md]

### X.2 Ambiente de Testes

[Referência: benchmarks/outputs/comparison/benchmark_report.md]

### X.3 Resultados

#### Tabela X.1: Performance por Ambiente
[CSV convertido para tabela]

#### Figura X.1: Latência Média
![](../benchmarks/outputs/comparison/plots/line_*.png)

### X.4 Análise

[Seu próprio texto, usando dados de BENCHMARK_SUMMARY.md]

### X.5 Conclusões

[Discussão usando CHANGELOG_BENCHMARKS.md]
```

---

## 🔗 Links para Dados Originais

Se quiser dados mais detalhados:

```
Dados brutos:        benchmarks/outputs/comparison/runs_raw.csv
Resumo tabular:      benchmarks/outputs/comparison/summary_by_env_model_batch.csv
Speedup:             benchmarks/outputs/comparison/speedup_vs_desktop_legion.csv
Gráficos:            benchmarks/outputs/comparison/plots/
Guia experimental:   benchmarks/BENCHMARKING_GUIDE.md
```

---

## 📋 Checklist para TCC

- [ ] Copiar `BENCHMARK_SUMMARY.md` como base
- [ ] Incluir 3-5 gráficos de `plots/`
- [ ] Criar tabelas a partir de CSVs
- [ ] Referenciar `BENCHMARKING_GUIDE.md` como metodologia
- [ ] Mention DialoGPT-Nano, Qwen-Orin, Phi-Desktop como recomendações
- [ ] Adicionar análise dos gráficos
- [ ] Verificar se todos os dados fazem sentido

---

**Última atualização:** 2026-04-13
