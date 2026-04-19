"""
ESTRUTURA CRIADA - Resumo Rápido
"""

# 📊 Pasta: benchmarks/plots_scripts/ (SCRIPTS PYTHON)
# ├─ data_loader.py       → Carrega e agrega todos os JSONs dos testes
# ├─ plot_01_env_performance.py   → Latência + Throughput por Ambiente
# ├─ plot_02_model_comparison.py  → DialoGPT vs Qwen vs Phi por Env
# ├─ plot_03_accuracy_by_batch.py → Acurácia consistente entre 6 batches
# ├─ plot_04_latency_distribution.py → Boxplot de variabilidade
# ├─ plot_05_cross_env_speedup.py → Speedup vs Desktop Legion baseline
# ├─ plot_06_pdi_vs_slm.py        → Qual componente é gargalo
# └─ generate_all.py      → Roda TODOS os plots + gera HTML

# 📁 Pasta: benchmarks/plots_output/ (SAÍDA)
# ├─ 01_env_performance.png
# ├─ 02_model_comparison.png
# ├─ 03_accuracy_by_batch.png
# ├─ 04_latency_distribution.png
# ├─ 05_cross_env_speedup.png
# ├─ 06_pdi_vs_slm.png
# └─ index.html            → Relatório interativo (abrir no navegador)

# 📖 Documentação
# ├─ README_PLOTS.md       → Guia completo de uso
# └─ generate_plots.sh     → Script shell para facilitar execução


"""
COMO USAR - 3 Formas
"""

# FORMA 1: Gerar TUDO (Recomendado)
# ════════════════════════════════════════════════════════
cd benchmarks/plots_scripts
poetry run python generate_all.py
# ✅ Gera 6 PNGs + relatório HTML
# ✅ Salva em: benchmarks/plots_output/
# ✅ Abra: benchmarks/plots_output/index.html no navegador


# FORMA 2: Gerar UM plot específico (para refazer)
# ════════════════════════════════════════════════════════
cd benchmarks/plots_scripts
poetry run python plot_01_env_performance.py      # Performance
poetry run python plot_02_model_comparison.py     # Modelos
poetry run python plot_03_accuracy_by_batch.py    # Acurácia
# etc...


# FORMA 3: Script shell automático
# ════════════════════════════════════════════════════════
cd benchmarks
bash generate_plots.sh
# ✅ Mesmo que FORMA 1, mas com output formatado


"""
DADOS UTILIZADOS
"""

# Carrega automaticamente de:
#
# outputs/jetson-nano/batch{1-6}/{dialogpt,qwen}/pipeline_test_*.json
# outputs/jetson-orin/batch{1-6}/{dialogpt,qwen,phi}/pipeline_test_*.json
# outputs/desktop-legion/batch{1-6}/{dialogpt,qwen,phi}/pipeline_test_*.json
#
# Cada JSON tem:
# - metadata: ambiente, modelo, device, batch
# - performance: PDI, SLM, latência total
# - statistics: accuracy, correct frames
# - frames: detalhes por imagem


"""
CADA GRÁFICO RESPONDE UMA PERGUNTA
"""

# 📈 Plot 01: Qual ambiente é mais rápido?
→ Latência SLM + throughput para Nano, Orin, Legion

# 📊 Plot 02: Qual modelo é melhor onde?
→ Latência e acurácia: DialoGPT (Nano), Qwen (Orin), Phi (Legion)

# ✅ Plot 03: Performa igual em todos os batches?
→ Acurácia consistente entre batch1..batch6

# 📦 Plot 04: Qual é a variabilidade de latência?
→ Boxplot: min/max/mediana/quartis com outliers

# 🚀 Plot 05: Quanto mais rápido/lento vs Desktop?
→ Speedup relativo: >1.0 = mais rápido, <1.0 = mais lento

# 🔧 Plot 06: O gargalo é PDI (visão) ou SLM (model)?
→ Comparação: tempo de extração de features vs inferência


"""
QUALIDADE DOS GRÁFICOS
"""

# ✅ Resolução: 300 DPI (pronto para TCC/impressão)
# ✅ Formato: PNG (suporta todos os editores)
# ✅ Cores: Consistentes entre gráficos
# ✅ Fontes: Legíveis em tamanho pequeno
# ✅ Legendas: Completas e contextualizadas
# ✅ Relatório HTML: Visualização + referências


"""
PRÓXIMOS PASSOS (OPCIONAIS)
"""

# 1. Customizar cores (editar dicts 'colors' nos scripts)
# 2. Adicionar novos plots (seguir template dos existentes)
# 3. Incorporar em apresentação (copiar PNGs)
# 4. Compartilhar relatório HTML com orientador
# 5. Gerar tabelas CSV para seções numéricas


# FIM 🎉
