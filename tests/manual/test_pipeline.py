"""
Teste Manual do Pipeline Completo
Gera JSON dos resultados simulando resposta para frontend
Uso: python tests/manual/test_pipeline.py
"""
import cv2
import json
import time
from pathlib import Path
from datetime import datetime
from PIL import Image
from app.pipeline.illumination_pipeline import IlluminationPipeline
from app.config.config import Config

def process_image(pipeline, image_path: Path, expected_label: str = None):
    """
    Processa uma imagem e retorna resultado completo
    
    Args:
        pipeline: Pipeline inicializado
        image_path: Caminho da imagem
        expected_label: Label esperado (para validação)
    
    Returns:
        dict: Resultado completo com métricas e tempos
    """
    # Carrega imagem com OpenCV (BGR)
    image_cv = cv2.imread(str(image_path))
    if image_cv is None:
        return {
            'filename': image_path.name,
            'error': 'Failed to load image',
            'status': 'error'
        }
    
    # Converte BGR para RGB e depois para PIL Image
    # Pipeline.diagnose() espera PIL Image RGB
    image_rgb = cv2.cvtColor(image_cv, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image_rgb)
    
    # Processa com timing
    start_time = time.time()
    
    try:
        # Diagnóstico completo (com LLM)
        result = pipeline.diagnose(image)
        
        processing_time = time.time() - start_time
        
        # Monta resposta no formato frontend
        response = {
            'filename': image_path.name,
            'timestamp': datetime.now().isoformat(),
            'processing_time_seconds': round(processing_time, 3),
            
            # Status e Risco
            'status': result['status'],
            'risk_level': result['risk_level'],
            
            # Métricas de Iluminação
            'metrics': {
                'illumination': {
                    'score': round(result['metrics']['illumination'], 3),
                    'label': result['metrics']['illumination_label'],
                    'mean_brightness': round(result['metrics']['mean_brightness'], 3),
                },
                'details': result.get('illumination_details', {})
            },
            
            # Explicação do LLM
            'explanation': result['explanation'],
            
            # Recomendações
            'recommendations': result.get('recommendations', []),
            
            # Regras acionadas
            'triggered_rules': result.get('triggered_rules', []),
            
            # Validação (se fornecido label esperado)
            'validation': {
                'expected_label': expected_label,
                'predicted_label': result['metrics']['illumination_label'],
                'correct': result['metrics']['illumination_label'] == expected_label if expected_label else None
            }
        }
        
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        return {
            'filename': image_path.name,
            'timestamp': datetime.now().isoformat(),
            'processing_time_seconds': round(processing_time, 3),
            'error': str(e),
            'status': 'error'
        }


def main():
    """Executa teste completo do pipeline"""
    
    print("\n" + "=" * 80)
    print("TESTE MANUAL DO PIPELINE - SIMULAÇÃO FRONTEND")
    print("=" * 80)
    
    # Mapeamento de labels esperados para imagens normal
    # (baseado nos scores do test_illumination.py)
    normal_expected_labels = {
        'normal_image1.jpg': 'adequate',   # score ~0.734
        'normal_image2.jpg': 'acceptable',  # score ~0.5-0.7
        'normal_image3.jpg': 'adequate',   # score ~0.797
        'normal_image4.jpg': 'adequate',   # score ~0.785
        'normal_image5.jpg': 'acceptable'   # score ~0.5-0.7
    }
    
    # Configura testes
    test_cases = [
        {
            'category': 'overexposed',
            'expected_label': 'overexposed',
            'images': [
                'data/illumination/bright_overexposed/bright_image1.jpg',
                'data/illumination/bright_overexposed/bright_image2.jpg',
                'data/illumination/bright_overexposed/bright_image3.jpg',
                'data/illumination/bright_overexposed/bright_image4.jpg',
                'data/illumination/bright_overexposed/bright_image5.jpg',
            ]
        },
        {
            'category': 'underexposed',
            'expected_label': 'underexposed',
            'images': [
                'data/illumination/dark_underexposed/dark_image1.jpg',
                'data/illumination/dark_underexposed/dark_image2.jpg',
                'data/illumination/dark_underexposed/dark_image3.jpg',
                'data/illumination/dark_underexposed/dark_image4.jpg',
                'data/illumination/dark_underexposed/dark_image5.jpg',
            ]
        },
        {
            'category': 'normal (adequate + acceptable)',
            'expected_label': None,  # Label varia por imagem
            'images': [
                'data/illumination/normal/normal_image1.jpg',  # adequate
                'data/illumination/normal/normal_image2.jpg',  # acceptable
                'data/illumination/normal/normal_image3.jpg',  # adequate
                'data/illumination/normal/normal_image4.jpg',  # adequate
                'data/illumination/normal/normal_image5.jpg',  # acceptable
            ]
        }
    ]
    
    # Inicializa pipeline
    print("\n1. Inicializando pipeline...")
    config = Config()
    model_type = config.get('models.default', 'qwen')
    use_4bit = config.get('models.use_4bit', True)
    device = config.get('models.device', 'cuda')
    
    print(f"   Model: {model_type}")
    print(f"   4-bit: {use_4bit}")
    print(f"   Device: {device}")
    
    pipeline = IlluminationPipeline(
        model_type=model_type,
        use_4bit=use_4bit,
        device=device
    )
    
    # Processa todas as imagens
    print(f"\n2. Processando imagens...\n")
    
    all_results = []
    total_images = sum(len(tc['images']) for tc in test_cases)
    processed = 0
    correct = 0
    total_time = 0
    
    for test_case in test_cases:
        category = test_case['category']
        expected_label = test_case['expected_label']
        
        print(f"\n{'─' * 80}")
        print(f"Categoria: {category.upper()}")
        print(f"{'─' * 80}")
        
        for img_path in test_case['images']:
            path = Path(img_path)
            if not path.exists():
                print(f"  ❌ {path.name} - Não encontrada")
                continue
            
            processed += 1
            print(f"\n  [{processed}/{total_images}] Processando {path.name}...")
            
            # Determina label esperado (usa mapeamento para imagens normal)
            if path.name in normal_expected_labels:
                expected_label_for_image = normal_expected_labels[path.name]
            else:
                expected_label_for_image = expected_label
            
            # Processa imagem
            result = process_image(pipeline, path, expected_label_for_image)
            all_results.append(result)
            
            # Atualiza estatísticas
            if result.get('status') != 'error':
                total_time += result['processing_time_seconds']
                if result['validation']['correct']:
                    correct += 1
                
                # Mostra resumo
                status_emoji = "✓" if result['status'] == 'pass' else "✗"
                validation_emoji = "✓" if result['validation']['correct'] else "✗"
                
                print(f"     Status: {status_emoji} {result['status'].upper()} ({result['risk_level']})")
                print(f"     Label: {validation_emoji} {result['metrics']['illumination']['label']}")
                print(f"     Score: {result['metrics']['illumination']['score']:.3f}")
                print(f"     Tempo: {result['processing_time_seconds']:.2f}s")
                print(f"     Explicação: {result['explanation'][:80]}...")
                
                if result['recommendations']:
                    print(f"     Recomendações: {len(result['recommendations'])}")
            else:
                print(f"     ❌ Erro: {result.get('error', 'Unknown')}")
    
    # Calcula estatísticas finais
    avg_time = total_time / processed if processed > 0 else 0
    accuracy = (correct / processed * 100) if processed > 0 else 0
    
    # Monta resultado final para frontend
    frontend_response = {
        'metadata': {
            'test_name': 'Pipeline Complete Test',
            'timestamp': datetime.now().isoformat(),
            'model': model_type,
            'device': device,
            'quantization': '4-bit' if use_4bit else 'fp16/fp32'
        },
        'statistics': {
            'total_images': total_images,
            'processed': processed,
            'successful': correct,
            'failed': processed - correct,
            'accuracy_percent': round(accuracy, 2),
            'total_time_seconds': round(total_time, 2),
            'average_time_seconds': round(avg_time, 2),
            'throughput_images_per_second': round(1.0 / avg_time, 3) if avg_time > 0 else 0
        },
        'results': all_results
    }
    
    # Salva JSON
    output_dir = Path('outputs')
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f'pipeline_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(frontend_response, f, indent=2, ensure_ascii=False)
    
    # Mostra resumo final
    print(f"\n{'=' * 80}")
    print("RESUMO FINAL")
    print(f"{'=' * 80}")
    print(f"\n📊 Estatísticas:")
    print(f"   Total de imagens: {total_images}")
    print(f"   Processadas: {processed}")
    print(f"   Corretas: {correct}")
    print(f"   Acurácia: {accuracy:.1f}%")
    print(f"\n⏱️  Desempenho:")
    print(f"   Tempo total: {total_time:.2f}s")
    print(f"   Tempo médio: {avg_time:.2f}s por imagem")
    print(f"   Throughput: {1.0/avg_time:.2f} imagens/segundo" if avg_time > 0 else "   Throughput: N/A")
    print(f"\n💾 Resultado salvo em: {output_file}")
    print(f"\n✅ Teste concluído!")
    print("=" * 80)
    
    # Mostra preview do JSON
    print(f"\n📄 Preview do JSON gerado (primeiros 50 linhas):")
    print("─" * 80)
    with open(output_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:50], 1):
            print(line.rstrip())
        if len(lines) > 50:
            print(f"... ({len(lines) - 50} linhas restantes)")
    print("─" * 80)


if __name__ == "__main__":
    main()
