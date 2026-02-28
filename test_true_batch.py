"""
Teste de TRUE BATCH INFERENCE
Compara batch tradicional (sequencial) vs true batch (paralelo)
"""
import cv2
import time
from pathlib import Path
from PIL import Image
from app.pipeline.illumination_pipeline import IlluminationPipeline

def main():
    print("\n" + "="*80)
    print("TESTE: TRUE BATCH INFERENCE")
    print("="*80)
    
    # Seleciona imagens de teste
    test_images = [
        Path('data/illumination/bright_overexposed/bright_image1.jpg'),
        Path('data/illumination/dark_underexposed/dark_image1.jpg'),
        Path('data/illumination/normal/normal_image1.jpg'),
        Path('data/illumination/normal/normal_image2.jpg'),
        Path('data/illumination/bright_overexposed/bright_image2.jpg'),
        Path('data/illumination/dark_underexposed/dark_image2.jpg'),
        Path('data/illumination/normal/normal_image3.jpg'),
        Path('data/illumination/normal/normal_image4.jpg'),
    ]
    
    test_images = [p for p in test_images if p.exists()]
    print(f"\nUsando {len(test_images)} imagens de teste")
    
    # Inicializa pipeline
    print("\nInicializando pipeline...")
    pipeline = IlluminationPipeline(model_type='qwen', use_4bit=True, device='cuda')
    
    # FASE 1: Extrai métricas
    print("\n" + "─"*80)
    print("FASE 1: Extração de Métricas PDI")
    print("─"*80)
    
    phase1_start = time.time()
    images_pil = []
    for img_path in test_images:
        img = cv2.imread(str(img_path))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        images_pil.append(pil_img)
    
    metrics_list = pipeline.extract_metrics_batch(images_pil)
    phase1_time = time.time() - phase1_start
    
    print(f"\n✓ Fase 1 concluída: {phase1_time:.2f}s ({phase1_time/len(test_images)*1000:.0f}ms/imagem)")
    for i, m in enumerate(metrics_list):
        print(f"  [{i+1}] {m['illumination_label']} (score: {m['illumination']:.3f})")
    
    # TESTE: Processa 3x para obter média estável
    print("\n" + "="*80)
    print("FASE 2: Diagnose LLM com TRUE BATCH INFERENCE")
    print("="*80)
    
    print("\nAquecendo modelo (primeira chamada inclui carregamento)...")
    _ = pipeline.diagnose_from_metrics_batch(metrics_list)
    
    print("\nExecutando 3 rodadas para média estável...")
    batch_times = []
    
    for run in range(1, 4):
        print(f"\n--- Rodada {run}/3 ---")
        start = time.time()
        results = pipeline.diagnose_from_metrics_batch(metrics_list)
        elapsed = time.time() - start
        batch_times.append(elapsed)
        
        avg_per_scene = elapsed / len(metrics_list)
        print(f"Tempo total: {elapsed:.2f}s")
        print(f"Tempo médio: {avg_per_scene:.2f}s/cena")
        print(f"Throughput: {len(metrics_list)/elapsed:.2f} cenas/segundo")
    
    # ESTATÍSTICAS FINAIS
    print("\n" + "="*80)
    print("RESULTADOS FINAIS (TRUE BATCH INFERENCE)")
    print("="*80)
    
    avg_batch_time = sum(batch_times) / len(batch_times)
    min_batch_time = min(batch_times)
    max_batch_time = max(batch_times)
    
    print(f"\nTotal de imagens: {len(test_images)}")
    print(f"\nFase 1 (PDI): {phase1_time:.2f}s ({phase1_time/len(test_images)*1000:.0f}ms/imagem)")
    print(f"\nFase 2 (LLM Batch):")
    print(f"  Melhor:  {min_batch_time:.2f}s ({min_batch_time/len(test_images):.2f}s/cena)")
    print(f"  Média:   {avg_batch_time:.2f}s ({avg_batch_time/len(test_images):.2f}s/cena)")
    print(f"  Pior:    {max_batch_time:.2f}s ({max_batch_time/len(test_images):.2f}s/cena)")
    
    total_avg = phase1_time + avg_batch_time
    print(f"\nTempo total médio: {total_avg:.2f}s")
    print(f"Tempo médio/imagem: {total_avg/len(test_images):.2f}s")
    
    # Comparação com baseline sequencial (estimativa)
    print("\n" + "─"*80)
    print("COMPARAÇÃO vs SEQUENCIAL")
    print("─"*80)
    
    # Baseline: ~5.28s/imagem (do teste anterior)
    baseline_per_image = 5.28
    baseline_total = baseline_per_image * len(test_images)
    batch_per_image = total_avg / len(test_images)
    
    improvement = ((baseline_total - total_avg) / baseline_total) * 100
    speedup = baseline_per_image / batch_per_image
    
    print(f"\nMétodo Sequencial (baseline):")
    print(f"  ~{baseline_per_image:.2f}s/imagem × {len(test_images)} = ~{baseline_total:.2f}s total")
    
    print(f"\nMétodo TRUE BATCH:")
    print(f"  {batch_per_image:.2f}s/imagem × {len(test_images)} = {total_avg:.2f}s total")
    
    if improvement > 0:
        print(f"\n🚀 TRUE BATCH é {improvement:.1f}% MAIS RÁPIDO")
        print(f"   Speedup: {speedup:.2f}x")
    else:
        print(f"\n⚠️  TRUE BATCH é {abs(improvement):.1f}% MAIS LENTO")
    
    # Mostra algumas explicações
    print("\n" + "─"*80)
    print("EXEMPLOS DE EXPLICAÇÕES GERADAS")
    print("─"*80)
    
    for i, (result, img_path) in enumerate(zip(results[:3], test_images[:3])):
        print(f"\n[{i+1}] {img_path.name}")
        print(f"Status: {result['status'].upper()} | {result['metrics']['illumination_label']}")
        print(f"Explicação: {result['explanation']}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
