# Atualização de Benchmarks - Suporte para 3 Ambientes

## Resumo das Mudanças

O sistema de benchmarks foi atualizado para incluir suporte a **três ambientes de deployment**:
- **Desktop Legion** (baseline de referência)
- **Jetson Nano** (dispositivo edge antigo)
- **Jetson Orin** (dispositivo edge novo)

## Arquivos Modificados

### 1. `benchmark_jetson_vs_legion.py` (Principal)
**Mudanças:**
- Agora aceita 3 diretórios de entrada em vez de 2:
  - `--desktop-legion-dir` (padrão: `outputs/desktop-legion`)
  - `--jetson-nano-dir` (padrão: `outputs/jetson-nano`)
  - `--jetson-orin-dir` (padrão: `outputs/jetson-orin`)

- Função `collect_records()` agora coleta de 3 ambientes
- Função `build_speedup()` foi refatorada para comparar múltiplos ambientes dinamicamente
- Função `write_markdown()` gera tabelas dinâmicas baseadas em dados disponíveis
- Função `write_csv()` aprimorada para lidar com chaves heterogêneas
- Plots atualizados para mostrar 3 ambientes:
  - Boxplot com 3 distribuições
  - Barras com cores diferentes por ambiente
  - Linhas de tendência por ambiente
  - Speedup dinâmico vs Desktop Legion

### 2. `generate_comparison_report.py` (Novo)
Script que gera um **relatório HTML visualmente atraente** com:
- Resumo geral com estatísticas agregadas
- Tabelas detalhadas de performance
- Comparação de speedup vs Desktop Legion
- Embedagem automática dos gráficos PNG
- Design responsivo com cores por ambiente

### 3. `update_benchmarks.sh` (Novo)
Script shell que automatiza todo o pipeline:
1. Executa `benchmark_jetson_vs_legion.py`
2. Executa `generate_comparison_report.py`
3. Exibe resumo dos arquivos gerados

## Como Usar

### Opção 1: Execução Manual
```bash
# Gerar benchmarks e plots
python benchmark_jetson_vs_legion.py

# Gerar relatório HTML
python generate_comparison_report.py
```

### Opção 2: Executar Tudo de Uma Vez
```bash
./update_benchmarks.sh
```

### Opção 3: Com Argumentos Customizados
```bash
python benchmark_jetson_vs_legion.py \
    --desktop-legion-dir outputs/desktop-legion \
    --jetson-nano-dir outputs/jetson-nano \
    --jetson-orin-dir outputs/jetson-orin \
    --out-dir outputs/benchmark_comparison \
    --no-plots  # opcional: pula geração de plots
```

## Arquivos de Saída

Todos os arquivos são gerados em `outputs/benchmark_comparison/`:

### Relatórios
- **`benchmark_report.html`** - Relatório interativo HTML (abrir no navegador)
- **`benchmark_report.md`** - Markdown com tabelas
- **`speedup_vs_desktop_legion.csv`** - Speedups comparativos
- **`summary_by_env_model_batch.csv`** - Agregação por ambiente/modelo/batch
- **`runs_raw.csv`** - Dados brutos de todas as execuções

### Gráficos (pasta `plots/`)
- **`boxplot_total_s_by_environment.png`** - Distribuição de latência total
- **`bar_slm_per_diag_mean.png`** - Latência SLM média
- **`line_total_s_mean_by_batch.png`** - Tendência por batch
- **`bar_speedup_vs_legion.png`** - Comparação de speedup

## Metadados Coletados

O sistema coleta e analisa:
- **Total_s** - Tempo total de execução
- **slm_total_s** - Tempo total de inferência SLM
- **slm_per_diagnosis_s** - Tempo médio por diagnóstico
- **pdi_total_ms** - Tempo total de processamento de imagens
- **pdi_per_image_ms** - Tempo médio por imagem
- **accuracy** - Acurácia das predições
- **target_met** - Se atingiu meta de performance
- **quantization** - Tipo de quantização usado
- **device** - Hardware específico

## Interpretação dos Resultados

### Speedup
- **< 1.0** = Ambiente é **mais rápido** que Desktop Legion
- **= 1.0** = Performance **igual** a Desktop Legion
- **> 1.0** = Ambiente é **mais lento** que Desktop Legion

### Exemplos
```
Jetson Orin Speedup Total: 0.987 → ~1% mais rápido
Jetson Nano Speedup Total: 42.5 → 42x mais lento
```

## Estrutura de Dados

### Ambientes Reconhecidos
```
outputs/
├── desktop-legion/  → Data de Desktop Legion
│   ├── batch1/
│   ├── batch2/
│   └── ...
├── jetson-nano/     → Data de Jetson Nano
│   ├── batch1/
│   └── ...
└── jetson-orin/     → Data de Jetson Orin
    ├── batch1/
    └── ...
```

Cada batch contém arquivos JSON no formato: `pipeline_test_YYYYMMDD_HHMMSS.json`

## Requisitos

- Python 3.10+
- matplotlib (para gráficos)
- Pasta `outputs/` com subpastas contendo JSONs de teste

## Troubleshooting

### matplotlib não instalado
```bash
pip install matplotlib
```

### Nenhum arquivo encontrado
Verifique se a estrutura de pastas está correta:
```bash
ls -la outputs/desktop-legion/*/pipeline_test_*.json | head
ls -la outputs/jetson-nano/*/pipeline_test_*.json | head
ls -la outputs/jetson-orin/*/pipeline_test_*.json | head
```

### CSV com colunas inconsistentes
O script agora suporta isso automaticamente - diferentes ambientes podem ter diferentes métricas disponíveis.

## Próximas Melhorias Possíveis

- [ ] Gráficos interativos com Plotly
- [ ] Exportação para Excel
- [ ] Análise de tendências ao longo do tempo
- [ ] Alertas para degradação de performance
- [ ] Comparação com baseline histórico
