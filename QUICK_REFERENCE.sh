#!/bin/bash
# Quick reference para atualizar benchmarks

# ============================================
# OPÇÃO 1: Rápido (uma linha)
# ============================================
./update_benchmarks.sh

# ============================================  
# OPÇÃO 2: Executar scripts individualmente
# ============================================
python benchmark_jetson_vs_legion.py
python generate_comparison_report.py

# ============================================
# VER RESULTADOS
# ============================================

# Abrir relatório HTML no navegador
open outputs/benchmark_comparison/benchmark_report.html              # macOS
xdg-open outputs/benchmark_comparison/benchmark_report.html         # Linux
start outputs/benchmark_comparison/benchmark_report.html            # Windows

# Ver markdown direto no terminal
cat outputs/benchmark_comparison/benchmark_report.md

# Ver dados CSV
head -10 outputs/benchmark_comparison/summary_by_env_model_batch.csv
head -10 outputs/benchmark_comparison/speedup_vs_desktop_legion.csv

# Ver todos os gráficos
open outputs/benchmark_comparison/plots/                            # macOS
xdg-open outputs/benchmark_comparison/plots/                        # Linux

# ============================================
# COM ARGUMENTOS CUSTOMIZADOS
# ============================================
python benchmark_jetson_vs_legion.py \
    --desktop-legion-dir outputs/desktop-legion \
    --jetson-nano-dir outputs/jetson-nano \
    --jetson-orin-dir outputs/jetson-orin \
    --out-dir outputs/benchmark_comparison \
    --no-plots  # opcional: pula geração de gráficos

# ============================================
# CLEAN UP (remover relatórios antigos)
# ============================================
rm -rf outputs/benchmark_comparison/plots/*
rm outputs/benchmark_comparison/*.csv
rm outputs/benchmark_comparison/*.html
rm outputs/benchmark_comparison/*.md

# ============================================
# ESTATÍSTICAS RÁPIDAS
# ============================================
wc -l outputs/benchmark_comparison/runs_raw.csv              # Total de execuções
ls -lh outputs/benchmark_comparison/ | tail -n +2| awk '{print $5, $9}'  # Tamanhos
