#!/bin/bash
# Quick Reference - Benchmark Commands
# Estruturado por modelo primário e ambiente

# ============================================
# FASE 1: SETUP INICIAL (uma vez)
# ============================================
mkdir -p outputs/benchmarks/{dialogpt-small,qwen,phi}/{jetson-nano,jetson-orin,desktop-rtx}/reports/plots

# ============================================
# FASE 2: TESTES PRIMÁRIOS (RECOMENDADOS)
# ============================================

# === JETSON NANO - DialoGPT-small (Primário) ===
# SSH: ssh jetson
# Executar 1 batch de teste (5 runs x 10 imagens)
python test_dialogpt_nano.py \
  --batch-id batch1 \
  --num-runs 5 \
  --images 10 \
  --output outputs/benchmarks/dialogpt-small/jetson-nano/batch1/

# Repetir para batch2, batch3 (ou automático):
for batch in batch1 batch2 batch3; do
  python test_dialogpt_nano.py \
    --batch-id $batch \
    --num-runs 5 \
    --output outputs/benchmarks/dialogpt-small/jetson-nano/$batch/
done

# === JETSON ORIN - Qwen (Primário) ===
# SSH: ssh farmaciaback (ou outro hostname)
# Executar 3 batches
for batch in batch1 batch2 batch3; do
  python test_qwen_orin.py \
    --batch-id $batch \
    --num-runs 5 \
    --output outputs/benchmarks/qwen/jetson-orin/$batch/
done

# === DESKTOP RTX (Legion/Workstation) - Phi-3 (Primário) ===
# Windows PowerShell:
for ($batch = 1; $batch -le 3; $batch++) {
  python test_phi_desktop.py `
    --batch-id "batch$batch" `
    --num-runs 5 `
    --output "./outputs/benchmarks/phi/desktop-rtx/batch$batch/"
}
# ou Linux/Mac:
for batch in batch1 batch2 batch3; do
  python test_phi_desktop.py \
    --batch-id $batch \
    --num-runs 5 \
    --output outputs/benchmarks/phi/desktop-rtx/$batch/
done

# ============================================
# GERAR RELATÓRIOS INDIVIDUAIS (POR MODELO)
# ============================================

# Após testes de cada modelo, gerar relatório consolidado:
python generate_benchmark_report.py \
  --model dialogpt-small \
  --environment jetson-nano \
  --input-dir outputs/benchmarks/dialogpt-small/jetson-nano/ \
  --output-dir outputs/benchmarks/dialogpt-small/jetson-nano/reports/

python generate_benchmark_report.py \
  --model qwen \
  --environment jetson-orin \
  --input-dir outputs/benchmarks/qwen/jetson-orin/ \
  --output-dir outputs/benchmarks/qwen/jetson-orin/reports/

python generate_benchmark_report.py \
  --model phi \
  --environment desktop-rtx \
  --input-dir outputs/benchmarks/phi/desktop-rtx/ \
  --output-dir outputs/benchmarks/phi/desktop-rtx/reports/

# ============================================
# GERAR RELATÓRIO CONSOLIDADO (CROSS-MODELO)
# ============================================
# Depois que todos os 3 primários estão prontos:
python generate_consolidated_benchmark_report.py \
  --models-dir outputs/benchmarks/ \
  --output outputs/benchmarks/cross_model_comparison/ \
  --title "AR Diagnostic - Modelo Recomendado por Ambiente"

# ============================================
# VER RESULTADOS
# ============================================

# Relatório consolidado (HTML)
open outputs/benchmarks/cross_model_comparison/report.html              # macOS
xdg-open outputs/benchmarks/cross_model_comparison/report.html         # Linux
start outputs/benchmarks/cross_model_comparison/report.html            # Windows

# Relatórios por modelo (Markdown)
cat outputs/benchmarks/dialogpt-small/jetson-nano/reports/summary.md
cat outputs/benchmarks/qwen/jetson-orin/reports/summary.md
cat outputs/benchmarks/phi/desktop-rtx/reports/summary.md

# Gráficos (todos os ambientes)
open outputs/benchmarks/*/*/reports/plots/                  # macOS
xdg-open outputs/benchmarks/*/*/reports/plots/             # Linux

# ============================================
# FASE 3: TESTES ALTERNATIVOS (OPCIONAIS)
# ============================================
# Se tempo permitir, testar modelos alternativos:

# Phi-3 em Jetson Orin (teste curiosidade)
for batch in batch1 batch2 batch3; do
  python test_phi_orin.py \
    --batch-id $batch \
    --num-runs 5 \
    --output outputs/benchmarks/phi/jetson-orin/$batch/
done

# Qwen em Desktop RTX (teste velocidade vs Phi)
for batch in batch1 batch2 batch3; do
  python test_qwen_desktop.py \
    --batch-id $batch \
    --num-runs 5 \
    --output outputs/benchmarks/qwen/desktop-rtx/$batch/
done

# DialoGPT em Jetson Orin (teste curiosidade)
for batch in batch1 batch2 batch3; do
  python test_dialogpt_orin.py \
    --batch-id $batch \
    --num-runs 5 \
    --output outputs/benchmarks/dialogpt-small/jetson-orin/$batch/
done

# ============================================
# EXTRAIR ESTATÍSTICAS RÁPIDAS
# ============================================

# Latência média por modelo/ambiente
echo "=== Latência Média (ms/imagem) ==="
find outputs/benchmarks -name "summary.json" -exec grep -h "mean_latency_ms" {} \; | paste - <(echo "DialogPT-Nano; Qwen-Orin; Phi-RTX")

# Throughput médio
echo "=== Throughput Médio (imgs/sec) ==="
find outputs/benchmarks -name "summary.json" -exec grep -h "mean_throughput" {} \; | paste - <(echo "DialogPT-Nano; Qwen-Orin; Phi-RTX")

# Taxa de validação
echo "=== Taxa de Validação LLM (%) ==="
find outputs/benchmarks -name "summary.json" -exec grep -h "total_quality_rate" {} \; | paste - <(echo "DialogPT-Nano; Qwen-Orin; Phi-RTX")

# ============================================
# LIMPEZA (remover dados antigos)
# ============================================
rm -rf outputs/benchmarks/*/*/plots/*
rm -rf outputs/benchmarks/*/*/
# Ou remover tudo:
rm -rf outputs/benchmarks/

# ============================================
# LEGADO (compatibilidade)
# ============================================
# Comandos antigos ainda funcionam:
python benchmark_jetson_vs_legion.py
python generate_comparison_report.py
open outputs/benchmark_comparison/benchmark_report.html  # Ver relatório antigo
