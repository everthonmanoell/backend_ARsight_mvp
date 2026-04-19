# 📊 Benchmark Plots - Scripts para Gráficos do TCC

Estrutura modular para geração de gráficos de benchmark com dados dos testes de pipeline em Jetson Nano, Jetson Orin e Desktop Legion.

## 📁 Estrutura

```
benchmarks/
├── plots_scripts/          # Scripts Python para geração de plots
│   ├── __init__.py
│   ├── data_loader.py      # Carrega dados dos JSONs
│   ├── plot_01_env_performance.py      # Latência e throughput por ambiente
│   ├── plot_02_model_comparison.py     # Comparação entre modelos
│   ├── plot_03_accuracy_by_batch.py    # Acurácia por batch
│   ├── plot_04_latency_distribution.py # Distribuição boxplot
│   ├── plot_05_cross_env_speedup.py    # Speedup vs baseline
│   ├── plot_06_pdi_vs_slm.py           # Comparação componentes
│   └── generate_all.py     # Coordenador - roda todos os plots
│
├── plots_output/           # Saída - gráficos PNG + relatório HTML
│   ├── 01_env_performance.png
│   ├── 02_model_comparison.png
│   ├── 03_accuracy_by_batch.png
│   ├── 04_latency_distribution.png
│   ├── 05_cross_env_speedup.png
│   ├── 06_pdi_vs_slm.png
│   └── index.html          # Relatório HTML com todos os gráficos
│
└── README.md               # Este arquivo
```

## 🚀 Como Usar

### Opção 1: Gerar Todos os Plots (Recomendado)

```bash
cd benchmarks/plots_scripts
poetry run python generate_all.py
```

Isso vai:
1. ✅ Carregar todos os dados dos JSONs em `outputs/`
2. ✅ Gerar 6 gráficos PNG (300 DPI, prontos para TCC)
3. ✅ Criar um relatório HTML com todos os gráficos
4. ✅ Salvar tudo em `benchmarks/plots_output/`

**Resultado:** Abra `benchmarks/plots_output/index.html` no navegador!

### Opção 2: Gerar Um Plot Específico

Se quiser refazer um gráfico individual:

```bash
cd benchmarks/plots_scripts

# Performance por Ambiente
poetry run python plot_01_env_performance.py

# Comparação por Modelo
poetry run python plot_02_model_comparison.py

# Acurácia por Batch
poetry run python plot_03_accuracy_by_batch.py

# Distribuição de Latência
poetry run python plot_04_latency_distribution.py

# Speedup Cross-Environment
poetry run python plot_05_cross_env_speedup.py

# PDI vs SLM
poetry run python plot_06_pdi_vs_slm.py
```

Cada script salva a imagem PNG no diretório atual.

## 📊 Descripção dos Gráficos

### 1. **Performance por Ambiente** (`01_env_performance.png`)
- **O que mostra:** Latência SLM e throughput para cada ambiente
- **Por que importa:** Identifica qual ambiente é mais rápido
- **Métrica:** Tempo em segundos (menor = melhor)

### 2. **Comparação por Modelo** (`02_model_comparison.png`)
- **O que mostra:** Latência e acurácia de cada modelo em cada ambiente
- **Por que importa:** Valida qual modelo é melhor onde
- **Modelos:** DialoGPT, Qwen, Phi (nem todos em todos os ambientes)

### 3. **Acurácia por Batch** (`03_accuracy_by_batch.png`)
- **O que mostra:** Consistência de acurácia entre os 6 batches
- **Por que importa:** Verifica se não há degeneração em batches específicos
- **Esperado:** Todas as linhas acima de 99%

### 4. **Distribuição de Latência** (`04_latency_distribution.png`)
- **O que mostra:** Boxplot com min/max/mediana/quartis
- **Por que importa:** Visualiza variabilidade e outliers
- **Linha vermelha:** Target de 1.0s

### 5. **Speedup Cross-Environment** (`05_cross_env_speedup.png`)
- **O que mostra:** Performance relativa vs Desktop Legion (baseline)
- **Por que importa:** Quantifica "quanto mais rápido/lento" cada env é
- **Valor > 1.0:** Mais rápido que desktop
- **Valor < 1.0:** Mais lento que desktop

### 6. **PDI vs SLM** (`06_pdi_vs_slm.png`)
- **O que mostra:** Tempo gasto em visão computacional (PDI) vs modelo (SLM)
- **Por que importa:** Identifica o gargalo entre os dois componentes
- **Insights:** Se SLM é muito maior, otimizar modelo; se PDI é grande, otimizar extração de features

## 📈 Dados Usados

Os scripts carregam JSONs de:
- `outputs/jetson-nano/batch{1-6}/(dialogpt|qwen)/pipeline_test_*.json`
- `outputs/jetson-orin/batch{1-6}/(dialogpt|qwen|phi)/pipeline_test_*.json`
- `outputs/desktop-legion/batch{1-6}/(dialogpt|qwen|phi)/pipeline_test_*.json`

Cada JSON contém:
- **metadata:** Environment, modelo, device, batch
- **performance:** Timings (PDI, SLM, total)
- **statistics:** Accuracy, runs corretos
- **frames:** Detalhes por imagem

## 🔧 Customização

### Modificar Cores
Edite os dicts `colors` em cada script:
```python
colors = {
    "jetson-nano": "#FF6B6B",
    "jetson-orin": "#4ECDC4",
    "desktop-legion": "#45B7D1",
}
```

### Modificar Resolução de Saída
Em cada script, procure por:
```python
plt.savefig(output_file, dpi=300, bbox_inches="tight")
```
Mudar `dpi=300` para outro valor (ex: `dpi=150` para preview rápido).

### Adicionar Novos Plots
1. Copie o template de `plot_0X_*.py`
2. Modifique a função `plot_xxx()` com sua lógica
3. Importe em `generate_all.py` e adicione à lista `plots`

## 📋 Requisitos

Dependências (já em `pyproject.toml`):
```
matplotlib >= 3.5
numpy >= 1.21
```

Para usar poetry:
```bash
poetry install
poetry run python generate_all.py
```

Ou com pip:
```bash
pip install matplotlib numpy
python generate_all.py
```

## 📤 Exportando para TCC

### Copiar PNGs
```bash
# Copiar gráficos individuais para a tese
cp benchmarks/plots_output/*.png ../tcc_figures/

# Ou copiar para pasta compartilhada
cp benchmarks/plots_output/*.png /mnt/shared/tcc/plots/
```

### Usar Relatório HTML
Abra `benchmarks/plots_output/index.html` diretamente no navegador para:
- ✅ Visualização interativa
- ✅ Copiar/compartilhar com orientador
- ✅ Integrar em apresentação (screenshot)

### Dados CSV
Para adicionar tabelas na tese, use `data_loader.py`:
```python
from plots_scripts.data_loader import BenchmarkLoader

loader = BenchmarkLoader()
summary = loader.summary_by_env_model()  # Lista de dicts

# Exportar para CSV
import csv
with open("benchmark_summary.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=summary[0].keys())
    writer.writeheader()
    writer.writerows(summary)
```

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'matplotlib'"
```bash
poetry run pip install matplotlib numpy
# ou
pip install matplotlib numpy
```

### "Nenhum dado carregado / Gráfico vazio"
Verifique se JSONs existem:
```bash
ls -la outputs/jetson-nano/batch1/
# Deve mostrar arquivos .json
```

### Gráficos com cores erradas
Edite as variáveis `colors` nos scripts.

### Imagens muito pequenas/grandes
Modifique `figsize` em cada plot:
```python
fig, ax = plt.subplots(figsize=(12, 6))  # Aumentar/diminuir
```

## 📧 Sugestões

Tem ideia de um novo gráfico? Crie um novo arquivo `plot_0X_*.py` seguindo o padrão dos existentes e abra um PR! 

---

**Última atualização:** Abril 2026  
**Status:** ✅ Todos os plots funcionando  
**Próximos passos:** Integrar com mais análises (correlações, regressões, etc)
