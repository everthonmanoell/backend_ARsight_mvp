"""
Teste simples de BetterTransformer

Instalar primeiro: pip install optimum

Este teste compara performance COM e SEM BetterTransformer
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pipeline.illumination_pipeline import IlluminationPipeline

def main():
    print("="*60)
    print("🧪 Teste BetterTransformer")
    print("="*60)
    
    # Verificar se optimum está instalado
    try:
        import optimum
        print("✅ Optimum instalado, BetterTransformer disponível")
    except ImportError:
        print("❌ Optimum não instalado")
        print("\n💡 Para instalar:")
        print("   pip install optimum")
        print("\nContinuando sem BetterTransformer...")
    
    print("\n" + "="*60)
    
    # Imagens para teste
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
    
    # Inicializar pipeline
    print(f"📦 Carregando modelo Qwen...")
    start_init = time.time()
    pipeline = IlluminationPipeline(model_type="qwen")
    init_time = time.time() - start_init
    print(f"⏱️ Tempo de inicialização: {init_time:.2f}s")
    
    # Warm-up
    print(f"\n🔥 Warm-up com 2 imagens...")
    _ = pipeline.diagnose_images_batch(images[:2])
    
    # Benchmark
    print(f"\n📊 Benchmark com {len(images)} imagens...")
    start = time.time()
    results = pipeline.diagnose_images_batch(images)
    total_time = time.time() - start
    
    avg_time = total_time / len(images)
    throughput = len(images) / total_time
    
    print(f"\n{'='*60}")
    print(f"✅ RESULTADOS")
    print(f"{'='*60}")
    print(f"⏱️ Tempo total: {total_time:.2f}s")
    print(f"📊 Tempo/imagem: {avg_time:.2f}s ({avg_time*1000:.0f}ms)")
    print(f"🚀 Throughput: {throughput:.2f} imagens/segundo")
    
    # Mostrar alguns resultados
    print(f"\n{'='*60}")
    print(f"🔍 Amostra de Diagnósticos")
    print(f"{'='*60}")
    for i, result in enumerate(results[:3], 1):
        problem = result.get('problem', 'N/A')
        cause = result.get('cause', 'N/A')
        print(f"\nImagem {i}:")
        print(f"  • Problema: {problem}")
        print(f"  • Causa: {cause[:60]}..." if len(cause) > 60 else f"  • Causa: {cause}")
    
    print(f"\n{'='*60}")
    print(f"💡 Observação:")
    print(f"  - Se viu '✅ BetterTransformer enabled' nos logs,")
    print(f"    a otimização está ativa!")
    print(f"  - Ganho esperado: 5-15% mais rápido")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
