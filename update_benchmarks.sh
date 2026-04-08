#!/bin/bash
# Script para atualizar todos os plots e benchmarks com dados de desktop-legion, jetson-nano e jetson-orin

set -e

VENV_PYTHON=".venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Erro: Virtual environment não encontrado em $VENV_PYTHON"
    exit 1
fi

echo "========================================"
echo "Atualizando benchmarks de performance"
echo "========================================"
echo ""

echo "1. Gerando comparação de performance (3 ambientes)..."
$VENV_PYTHON benchmark_jetson_vs_legion.py \
    --desktop-legion-dir outputs/desktop-legion \
    --jetson-nano-dir outputs/jetson-nano \
    --jetson-orin-dir outputs/jetson-orin \
    --out-dir outputs/benchmark_comparison

echo ""
echo "2. Gerando relatório HTML..."
$VENV_PYTHON generate_comparison_report.py

echo ""
echo "========================================"
echo "Benchmarks atualizados com sucesso!"
echo "========================================"
echo ""
echo "Arquivos gerados:"
echo "  - outputs/benchmark_comparison/benchmark_report.md (Markdown)"
echo "  - outputs/benchmark_comparison/benchmark_report.html (HTML)"
echo "  - outputs/benchmark_comparison/summary_by_env_model_batch.csv"
echo "  - outputs/benchmark_comparison/speedup_vs_desktop_legion.csv"
echo "  - outputs/benchmark_comparison/runs_raw.csv"
echo "  - outputs/benchmark_comparison/plots/ (gráficos PNG)"
echo ""
echo "Abra 'outputs/benchmark_comparison/benchmark_report.html' para visualizar!"
