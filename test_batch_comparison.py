"""
Comparação de Performance: Pipeline Tradicional vs Batch Processing
"""
import cv2
import json
import time
from pathlib import Path
from PIL import Image
from datetime import datetime
from app.pipeline.illumination_pipeline import IlluminationPipeline

def test_traditional_pipeline(pipeline, image_paths):
    """Método tradicional: processa cada imagem completamente"""
    print("\n" + "="*80)
    print("MÉTODO 1: PIPELINE TRADICIONAL (Imagem por imagem)")
    print("="*80)
    
    results = []
    start_total = time.time()
    
    for idx, img_path in enumerate(image_paths, 1):
        print(f"\n[{idx}/{len(image_paths)}] Processando {img_path.name}...")
        
        # Carrega e converte imagem
        img = cv2.imread(str(img_path))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        
        # Pipeline completo (PDI + LLM)
        start = time.time()
        result = pipeline.diagnose(pil_img)
        elapsed = time.time() - start
        
        result['filename'] = img_path.name
        result['processing_time'] = elapsed
        results.append(result)
        
        print(f"  ✓ {elapsed:.2f}s - {result['metrics']['illumination_label']}")
    
    total_time = time.time() - start_total
    avg_time = total_time / len(image_paths)
    
    print(f"\n{'─'*80}")
    print(f"Tempo total: {total_time:.2f}s")
    print(f"Tempo médio: {avg_time:.2f}s/imagem")
    print(f"{'─'*80}")
    
    return results, total_time, avg_time


def test_batch_pipeline(pipeline, image_paths):
    """Método em 2 fases: extrai métricas depois processa em batch"""
    print("\n" + "="*80)
    print("MÉTODO 2: BATCH PROCESSING (2 fases)")
    print("="*80)
    
    # FASE 1: Extração de métricas
    print("\n--- FASE 1: Extração de Métricas PDI ---")
    phase1_start = time.time()
    
    all_images = []
    for idx, img_path in enumerate(image_paths, 1):
        img = cv2.imread(str(img_path))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        all_images.append((img_path, pil_img))
    
    metrics_list = []
    for img_path, pil_img in all_images:
        metrics = pipeline.extract_metrics(pil_img)
        metrics['filename'] = img_path.name
        metrics_list.append(metrics)
        print(f"  ✓ {img_path.name} - {metrics['illumination_label']} (score: {metrics['illumination']:.3f})")
    
    phase1_time = time.time() - phase1_start
    print(f"\nFase 1 concluída: {phase1_time:.2f}s ({phase1_time/len(image_paths)*1000:.1f}ms/imagem)")
    
    # Salva métricas em JSON
    metrics_json = f"outputs/metrics_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(metrics_json, 'w', encoding='utf-8') as f:
        json.dump(metrics_list, f, indent=2, ensure_ascii=False)
    print(f"Métricas salvas em: {metrics_json}")
    
    # FASE 2: Processamento LLM em batch
    print("\n--- FASE 2: Diagnose LLM em Batch ---")
    phase2_start = time.time()
    
    results = pipeline.diagnose_from_metrics_batch(metrics_list)
    
    phase2_time = time.time() - phase2_start
    avg_llm_time = phase2_time / len(metrics_list)
    print(f"\nFase 2 concluída: {phase2_time:.2f}s ({avg_llm_time:.2f}s/cena)")
    
    # Adiciona filename aos resultados
    for result, metrics in zip(results, metrics_list):
        result['filename'] = metrics['filename']
    
    total_time = phase1_time + phase2_time
    avg_time = total_time / len(image_paths)
    
    print(f"\n{'─'*80}")
    print(f"Tempo Fase 1 (PDI): {phase1_time:.2f}s")
    print(f"Tempo Fase 2 (LLM): {phase2_time:.2f}s")
    print(f"Tempo total: {total_time:.2f}s")
    print(f"Tempo médio: {avg_time:.2f}s/imagem")
    print(f"{'─'*80}")
    
    return results, total_time, avg_time, phase1_time, phase2_time


def main():
    """Executa comparação"""
    print("\n" + "="*80)
    print("COMPARAÇÃO DE PERFORMANCE: TRADICIONAL vs BATCH")
    print("="*80)
    
    # Seleciona 5 imagens de teste
    test_images = [
        Path('data/illumination/bright_overexposed/bright_image1.jpg'),
        Path('data/illumination/dark_underexposed/dark_image1.jpg'),
        Path('data/illumination/normal/normal_image1.jpg'),
        Path('data/illumination/normal/normal_image2.jpg'),
        Path('data/illumination/bright_overexposed/bright_image2.jpg'),
    ]
    
    # Verifica se imagens existem
    test_images = [p for p in test_images if p.exists()]
    print(f"\nUsando {len(test_images)} imagens de teste")
    
    # Inicializa pipeline
    print("\nInicializando pipeline...")
    pipeline = IlluminationPipeline(model_type='qwen', use_4bit=True, device='cuda')
    
    # TESTE 1: Tradicional
    trad_results, trad_total, trad_avg = test_traditional_pipeline(pipeline, test_images)
    
    # Reinicia pipeline para comparação justa
    pipeline = IlluminationPipeline(model_type='qwen', use_4bit=True, device='cuda')
    
    # TESTE 2: Batch
    batch_results, batch_total, batch_avg, p1_time, p2_time = test_batch_pipeline(pipeline, test_images)
    
    # COMPARAÇÃO
    print("\n" + "="*80)
    print("COMPARAÇÃO FINAL")
    print("="*80)
    print(f"\nMétodo Tradicional:")
    print(f"  Tempo total: {trad_total:.2f}s")
    print(f"  Tempo médio: {trad_avg:.2f}s/imagem")
    
    print(f"\nMétodo Batch (2 fases):")
    print(f"  Fase 1 (PDI):  {p1_time:.2f}s ({p1_time/len(test_images)*1000:.0f}ms/imagem)")
    print(f"  Fase 2 (LLM):  {p2_time:.2f}s ({p2_time/len(test_images):.2f}s/cena)")
    print(f"  Tempo total:   {batch_total:.2f}s")
    print(f"  Tempo médio:   {batch_avg:.2f}s/imagem")
    
    improvement = ((trad_total - batch_total) / trad_total) * 100
    if improvement > 0:
        print(f"\n🚀 Batch é {improvement:.1f}% MAIS RÁPIDO")
    elif improvement < 0:
        print(f"\n⚠️  Batch é {abs(improvement):.1f}% MAIS LENTO")
    else:
        print(f"\n➖ Tempos equivalentes")
    
    print(f"\n{'='*80}")


if __name__ == "__main__":
    main()
