"""
Test Illumination Pipeline - MVP
Testa diagnóstico de iluminação em batch
"""

import sys
import os
import time
import csv
from pathlib import Path
from PIL import Image

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.pipeline.illumination_pipeline import IlluminationPipeline


def test_illumination_batch():
    """Testa pipeline com batch de imagens"""
    
    print("=" * 80)
    print("ILLUMINATION PIPELINE TEST - MVP")
    print("=" * 80)
    
    # Diretórios de teste
    test_dirs = {
        'underexposed': 'data/illumination/underexposed',
        'adequate': 'data/illumination/adequate',
        'overexposed': 'data/illumination/overexposed'
    }
    
    # Inicializa pipeline
    print("\n1. Initializing pipeline...")
    pipeline = IlluminationPipeline(model_type='qwen', use_4bit=True, device='cuda')
    
    # Coleta imagens
    test_images = []
    for label, dir_path in test_dirs.items():
        if os.path.exists(dir_path):
            for img_file in Path(dir_path).glob('*.jpg'):
                test_images.append({
                    'path': str(img_file),
                    'expected_label': label,
                    'filename': img_file.name
                })
    
    if not test_images:
        print("❌ No test images found!")
        return
    
    print(f"\n2. Found {len(test_images)} test images")
    print(f"   - Underexposed: {sum(1 for x in test_images if x['expected_label'] == 'underexposed')}")
    print(f"   - Adequate: {sum(1 for x in test_images if x['expected_label'] == 'adequate')}")
    print(f"   - Overexposed: {sum(1 for x in test_images if x['expected_label'] == 'overexposed')}")
    
    # Processa imagens
    print(f"\n3. Processing images...")
    print("=" * 80)
    
    results = []
    total_time = 0
    correct = 0
    
    for i, test_img in enumerate(test_images, 1):
        print(f"\n[{i}/{len(test_images)}] {test_img['filename']}")
        print(f"Expected: {test_img['expected_label']}")
        
        try:
            # Carrega imagem
            image = Image.open(test_img['path'])
            
            # Diagnose
            start_time = time.time()
            result = pipeline.diagnose(image)
            elapsed = time.time() - start_time
            total_time += elapsed
            
            # Verifica acurácia
            predicted_label = result['metrics']['illumination_label']
            is_correct = predicted_label == test_img['expected_label']
            if is_correct:
                correct += 1
            
            print(f"Predicted: {predicted_label} ({'✓' if is_correct else '✗'})")
            print(f"Status: {result['status'].upper()}")
            print(f"Time: {elapsed:.2f}s")
            print(f"Explanation: {result['explanation'][:100]}...")
            
            # Salva resultado
            results.append({
                'filename': test_img['filename'],
                'expected': test_img['expected_label'],
                'predicted': predicted_label,
                'status': result['status'],
                'correct': is_correct,
                'time': elapsed,
                'explanation': result['explanation']
            })
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                'filename': test_img['filename'],
                'expected': test_img['expected_label'],
                'predicted': 'ERROR',
                'status': 'error',
                'correct': False,
                'time': 0,
                'explanation': str(e)
            })
        
        print("-" * 80)
    
    # Estatísticas
    print(f"\n{'=' * 80}")
    print("TEST RESULTS")
    print("=" * 80)
    
    accuracy = (correct / len(test_images)) * 100 if test_images else 0
    avg_time = total_time / len(test_images) if test_images else 0
    throughput = len(test_images) / total_time if total_time > 0 else 0
    
    print(f"\nAccuracy: {correct}/{len(test_images)} ({accuracy:.1f}%)")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time: {avg_time:.2f}s per image")
    print(f"Throughput: {throughput:.2f} images/second")
    
    # Salva CSV
    output_file = 'outputs/mvp_test_results.csv'
    os.makedirs('outputs', exist_ok=True)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['filename', 'expected', 'predicted', 'status', 'correct', 'time', 'explanation'])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nResults saved to: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    test_illumination_batch()
