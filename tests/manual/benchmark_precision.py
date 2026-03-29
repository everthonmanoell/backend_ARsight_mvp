"""
Benchmark: Comparar velocidade entre FP32, FP16 e 4-bit Quantization
Testa o pipeline com diferentes configurações de precisão e quantização

Execução:
    poetry run python tests/manual/benchmark_precision.py
    
    ou

    .venv\Scripts\activate
    python tests/manual/benchmark_precision.py
"""
import json
import sys
import time
import os
import platform
from datetime import datetime
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config.config import Config, DEVICE, PLATFORM
from app.pipeline.illumination_pipeline import IlluminationPipeline

# ─────────────────────────────────────────────────────────────────────────────
# IMAGENS DE TESTE (Batch 1)
# ─────────────────────────────────────────────────────────────────────────────
BATCH_IMAGES = [
    ("data/uploads/20260315_143220/frame_00.jpg", "adequate"),
    ("data/uploads/20260315_143220/frame_01.jpg", "adequate"),
    ("data/uploads/20260315_143220/frame_02.jpg", "acceptable"),
    ("data/uploads/20260315_143220/frame_03.jpg", "acceptable"),
    ("data/uploads/20260315_143220/frame_04.jpg", "acceptable"),
    ("data/uploads/20260315_143220/frame_05.jpg", "adequate"),
    ("data/uploads/20260315_143220/frame_06.jpg", "adequate"),
    ("data/uploads/20260315_143220/frame_07.jpg", "adequate"),
    ("data/uploads/20260315_143220/frame_08.jpg", "adequate"),
    ("data/uploads/20260315_143220/frame_09.jpg", "adequate"),
]

def load_image(path: str):
    """Carrega imagem via PIL - tenta múltiplos caminhos."""
    if Path(path).exists():
        return Image.open(path)
    
    app_path = Path("/app") / path
    if app_path.exists():
        return Image.open(app_path)
    
    cwd_path = Path.cwd() / path
    if cwd_path.exists():
        return Image.open(cwd_path)
    
    return None

def sep(char="─", width=100):
    print(char * width)

def run_benchmark(model_type="qwen", precision="fp32", use_4bit=False):
    """
    Executa benchmark com configuração específica
    
    Args:
        model_type: "qwen" ou "phi"
        precision: "fp16" ou "fp32"
        use_4bit: True para 4-bit quantization
    
    Returns:
        dict com métricas de tempo
    """
    # Set environment variable for precision
    os.environ["MODEL_PRECISION"] = precision
    
    # Label para exibição
    if use_4bit:
        config_label = "4-BIT QUANTIZATION"
    elif precision == "fp16":
        config_label = "FP16"
    else:
        config_label = "FP32"
    
    print(f"\n📊 Teste: {config_label} (use_4bit={use_4bit})")
    sep("─", 100)
    
    # ─────────────────────────────────────────────────────────────────────────────
    # 1) INICIALIZAR PIPELINE
    # ─────────────────────────────────────────────────────────────────────────────
    print(f"[1/4] Inicializando pipeline...")
    t_init_start = time.perf_counter()
    
    try:
        # Force reload de config
        from importlib import reload
        import app.config.config as config_module
        reload(config_module)
        
        pipeline = IlluminationPipeline(
            model_type=model_type,
            use_4bit=use_4bit,
            device=DEVICE
        )
        pipeline._load_model()
        
        t_init = time.perf_counter() - t_init_start
        print(f"      ✅ Modelo carregado em {t_init:.2f}s")
    except Exception as e:
        print(f"      ❌ Erro na inicialização: {e}")
        return None
    
    # ─────────────────────────────────────────────────────────────────────────────
    # 2) CARREGAR IMAGENS
    # ─────────────────────────────────────────────────────────────────────────────
    print(f"[2/4] Carregando {len(BATCH_IMAGES)} imagens...")
    images, filenames, expected_labels = [], [], []
    
    for path_str, label in BATCH_IMAGES:
        img = load_image(path_str)
        if img:
            images.append(img)
            filenames.append(Path(path_str).name)
            expected_labels.append(label)
    
    if not images:
        print(f"      ❌ Nenhuma imagem encontrada")
        return None
    
    print(f"      ✅ {len(images)} imagens carregadas")
    
    # ─────────────────────────────────────────────────────────────────────────────
    # 3) FASE PDI (Visão Computacional)
    # ─────────────────────────────────────────────────────────────────────────────
    print(f"[3/4] Executando PDI (visão computacional)...")
    t_pdi = time.perf_counter()
    
    try:
        pdi_metrics = pipeline.extract_metrics_batch(images)
        t_pdi_elapsed = time.perf_counter() - t_pdi
        print(f"      ✅ PDI completo em {t_pdi_elapsed*1000:.1f}ms ({t_pdi_elapsed/len(images)*1000:.1f}ms/img)")
    except Exception as e:
        print(f"      ❌ Erro no PDI: {e}")
        return None
    
    # ─────────────────────────────────────────────────────────────────────────────
    # 4) FASE SLM (Model Inference + Summary)
    # ─────────────────────────────────────────────────────────────────────────────
    print(f"[4/4] Executando SLM (diagnóstico + summary)...")
    t_slm = time.perf_counter()
    
    try:
        diagnoses, summary = pipeline.diagnose_from_metrics_batch_with_summary(pdi_metrics)
        t_slm_elapsed = time.perf_counter() - t_slm
        per_diag = t_slm_elapsed / len(images)
        
        print(f"      ✅ SLM completo em {t_slm_elapsed:.2f}s ({per_diag*1000:.0f}ms/diagnóstico)")
    except Exception as e:
        print(f"      ❌ Erro no SLM: {e}")
        return None
    
    # ─────────────────────────────────────────────────────────────────────────────
    # RESULTADOS
    # ─────────────────────────────────────────────────────────────────────────────
    total_time = t_init + t_pdi_elapsed + t_slm_elapsed
    
    results = {
        "config": config_label,
        "precision": precision,
        "use_4bit": use_4bit,
        "model_type": model_type,
        "t_model_load": t_init,
        "t_pdi": t_pdi_elapsed,
        "t_slm": t_slm_elapsed,
        "t_per_diag": per_diag,
        "t_total": total_time,
        "n_images": len(images),
        "timestamp": datetime.now().isoformat()
    }
    
    return results

def main():
    sep("═", 100)
    print("🔧 BENCHMARK: FP32 vs FP16 vs 4-BIT QUANTIZATION")
    sep("═", 100)
    
    print(f"\n📱 Plataforma: {PLATFORM.upper()}")
    print(f"🖥️  Device: {DEVICE.upper()}")
    print(f"🕐 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    model_type = "qwen"  # ou "phi" se preferir
    
    all_results = []
    
    # ═════════════════════════════════════════════════════════════════════════════
    # TESTE 1: FP32 (baseline)
    # ═════════════════════════════════════════════════════════════════════════════
    result1 = run_benchmark(model_type=model_type, precision="fp32", use_4bit=False)
    if result1:
        all_results.append(result1)
    
    print("\n⏳ Aguardando 5 segundos antes do próximo teste...\n")
    time.sleep(5)
    
    # ═════════════════════════════════════════════════════════════════════════════
    # TESTE 2: FP16
    # ═════════════════════════════════════════════════════════════════════════════
    result2 = run_benchmark(model_type=model_type, precision="fp16", use_4bit=False)
    if result2:
        all_results.append(result2)
    
    print("\n⏳ Aguardando 5 segundos antes do próximo teste...\n")
    time.sleep(5)
    
    # ═════════════════════════════════════════════════════════════════════════════
    # TESTE 3: 4-BIT
    # ═════════════════════════════════════════════════════════════════════════════
    result3 = run_benchmark(model_type=model_type, precision="fp32", use_4bit=True)
    if result3:
        all_results.append(result3)
    
    # ═════════════════════════════════════════════════════════════════════════════
    # RELATÓRIO COMPARATIVO
    # ═════════════════════════════════════════════════════════════════════════════
    if not all_results:
        print("\n❌ Nenhum teste completou com sucesso")
        return
    
    print("\n\n")
    sep("═", 100)
    print("📈 RELATÓRIO COMPARATIVO")
    sep("═", 100)
    
    # Tabela com resultados
    print(f"\n{'Config':<20} {'Init(ms)':<12} {'PDI(ms)':<12} {'SLM(s)':<10} {'Per-Diag(ms)':<15} {'Total(s)':<10}")
    sep("─", 100)
    
    for r in all_results:
        print(f"{r['config']:<20} {r['t_model_load']*1000:>10.1f}  {r['t_pdi']*1000:>10.1f}  "
              f"{r['t_slm']:>8.2f}  {r['t_per_diag']*1000:>13.0f}  {r['t_total']:>8.2f}")
    
    # Cálculo de speedups
    print("\n")
    sep("─", 100)
    print("⚡ SPEEDUP (vs FP32 baseline):\n")
    
    baseline = all_results[0]['t_total']
    
    for i, r in enumerate(all_results):
        speedup = baseline / r['t_total']
        pct_faster = (1 - r['t_total']/baseline) * 100
        
        if i == 0:
            print(f"{r['config']:<20} → BASELINE (1.00x)")
        else:
            symbol = "⬆️ " if speedup > 1 else "⬇️ "
            print(f"{r['config']:<20} → {speedup:>4.2f}x  ({pct_faster:>+6.1f}%)")
    
    # Análise de economia de memória
    print("\n")
    sep("─", 100)
    print("💾 IMPACTO NA MEMÓRIA:\n")
    print("  FP32:       ~Baseline")
    print("  FP16:       ~50% menor (mantendo qualidade)")
    print("  4-BIT:      ~80% menor (quantização agressiva)\n")
    
    # Salvar resultados em JSON
    output_file = Path(__file__).parent.parent.parent / "outputs" / f"benchmark_precision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            "platform": PLATFORM,
            "device": DEVICE,
            "timestamp": datetime.now().isoformat(),
            "results": all_results
        }, f, indent=2)
    
    print(f"✅ Resultados salvos em: {output_file.relative_to(Path.cwd())}")
    
    sep("═", 100)
    print("✅ BENCHMARK COMPLETO\n")

if __name__ == "__main__":
    main()
