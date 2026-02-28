"""
Benchmark comparando diferentes otimizações avançadas:
1. Baseline (sem otimizações extras)
2. BetterTransformer
3. torch.compile()
"""

import sys
import time
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pipeline.illumination_pipeline import IlluminationPipeline

def test_optimization(enable_compile: bool = False, label: str = ""):
    """Testa performance com configuração específica"""
    print(f"\n{'='*60}")
    print(f"🧪 Testando: {label}")
    print(f"{'='*60}")
    
    # Inicializa pipeline
    start_init = time.time()
    pipeline = IlluminationPipeline(
        model_type="qwen",
        enable_compile=enable_compile
    )
    init_time = time.time() - start_init
    print(f"⏱️ Tempo de inicialização: {init_time:.2f}s")
    
    # Caminhos das imagens
    base_path = Path(__file__).parent.parent / "data" / "illumination"
    images = [
        str(base_path / "dark_underexposed" / "dark_image1.jpg"),
        str(base_path / "dark_underexposed" / "dark_image2.jpg"),
        str(base_path / "bright_overexposed" / "bright_image1.jpg"),
        str(base_path / "bright_overexposed" / "bright_image2.jpg"),
        str(base_path / "normal" / "normal_image1.jpg"),
        str(base_path / "normal" / "normal_image2.jpg"),
        str(base_path / "normal" / "normal_image3.jpg"),
        str(base_path / "normal" / "normal_image4.jpg"),
    ]
    
    # Warm-up (primeira inferência é mais lenta)
    print(f"🔥 Warm-up...")
    _ = pipeline.diagnose_images_batch(images)
    
    # Benchmark
    print(f"📊 Executando benchmark com {len(images)} imagens...")
    start = time.time()
    results = pipeline.diagnose_images_batch(images)
    total_time = time.time() - start
    
    avg_time = total_time / len(images)
    
    print(f"\n✅ Resultados: {label}")
    print(f"  • Tempo total: {total_time:.2f}s")
    print(f"  • Tempo/imagem: {avg_time:.2f}s ({avg_time*1000:.0f}ms)")
    print(f"  • Throughput: {len(images)/total_time:.2f} imagens/segundo")
    
    return {
        "label": label,
        "init_time": init_time,
        "total_time": total_time,
        "avg_time": avg_time,
        "throughput": len(images) / total_time
    }

def main():
    print("="*60)
    print("🚀 Benchmark de Otimizações Avançadas")
    print("="*60)
    
    results = []
    
    # 1. Baseline (sem otimizações extras)
    results.append(test_optimization(
        enable_compile=False,
        label="Baseline (sem otimizações extras)"
    ))
    
    # Small delay to clear GPU cache
    time.sleep(3)
    
    # 2. torch.compile()
    results.append(test_optimization(
        enable_compile=True,
        label="torch.compile() [modo: reduce-overhead]"
    ))
    
    # Comparação final
    print(f"\n{'='*60}")
    print("📈 COMPARAÇÃO FINAL")
    print(f"{'='*60}")
    
    baseline = results[0]
    for r in results[1:]:
        speedup = baseline["total_time"] / r["total_time"]
        improvement = (1 - r["avg_time"]/baseline["avg_time"]) * 100
        
        print(f"\n{r['label']}:")
        print(f"  • Tempo total: {r['total_time']:.2f}s")
        print(f"  • Avg/imagem: {r['avg_time']:.2f}s")
        print(f"  • Speedup: {speedup:.2f}x")
        print(f"  • Melhoria: {improvement:+.1f}%")
    
    print(f"\n{'='*60}")
    print("💡 Notas:")
    print("  • BetterTransformer é aplicado automaticamente se disponível")
    print("  • torch.compile() tem overhead de inicialização (~2-3min)")
    print("  • Primeira inferência sempre mais lenta (warm-up)")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
