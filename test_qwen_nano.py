#!/usr/bin/env python3
"""
Teste rápido Qwen Nano - testa carregamento do modelo e diagnóstico com 1 imagem real
Uso: python test_qwen_nano.py
"""

import logging
import time
import torch
from pathlib import Path
from PIL import Image

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_section(title: str):
    """Imprime seção formatada"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_cuda_info():
    """Imprime informações de CUDA/GPU"""
    print_section("GPU/CUDA INFO")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA Device: {torch.cuda.get_device_name(0)}")
        print(f"CUDA Compute Capability: {torch.cuda.get_device_capability(0)}")
        print(f"CUDA Version: {torch.version.cuda}")
        props = torch.cuda.get_device_properties(0)
        print(f"Total GPU Memory: {props.total_memory / 1e9:.2f} GB")
        print(f"GPU Memory Allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
    else:
        print("⚠️  CUDA NÃO DISPONÍVEL - rodando em CPU")
    print(f"PyTorch Version: {torch.__version__}")

def main():
    """Teste principal"""
    
    print_section("TESTE QWEN NANO - 1 IMAGEM REAL")
    print_cuda_info()
    
    # Verifica imagem
    image_path = Path("data/uploads/batch_20260404_145918_57ad92/frame_00.jpg")
    
    print_section("VERIFICAÇÃO DE IMAGEM")
    if image_path.exists():
        print(f"✅ Imagem encontrada: {image_path}")
        img = Image.open(image_path)
        print(f"   Tamanho: {img.size}")
        print(f"   Modo: {img.mode}")
    else:
        print(f"❌ Imagem NÃO encontrada: {image_path}")
        return
    
    # Inicializa pipeline
    print_section("CARREGANDO PIPELINE QWEN")
    start_pipeline = time.time()
    
    try:
        from app.pipeline.illumination_pipeline import IlluminationPipeline
        
        # Detecta se está em Jetson (pode definir manualmente se necessário)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        use_4bit = True  # Quantização para economizar VRAM
        
        logger.info(f"Inicializando pipeline com device={device}, quantização 4-bit={use_4bit}")
        pipeline = IlluminationPipeline(model_type='qwen', use_4bit=use_4bit, device=device)
        
        pipeline_time = time.time() - start_pipeline
        print(f"✅ Pipeline carregado em {pipeline_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Erro ao carregar pipeline: {e}")
        logger.exception("Detalhes do erro:")
        return
    
    # Carrega modelo (lazy loading)
    print_section("CARREGANDO MODELO QWEN")
    start_model = time.time()
    
    try:
        pipeline._load_model()
        model_time = time.time() - start_model
        print(f"✅ Modelo Qwen carregado em {model_time:.2f}s")
        
        if torch.cuda.is_available():
            print(f"   VRAM após carregamento: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
            
    except Exception as e:
        print(f"❌ Erro ao carregar modelo: {e}")
        logger.exception("Detalhes do erro:")
        return
    
    # Executa diagnóstico
    print_section("EXECUTANDO DIAGNÓSTICO (1 IMAGEM)")
    start_diag = time.time()
    
    try:
        result = pipeline.diagnose(image_path)
        diag_time = time.time() - start_diag
        
        print(f"✅ Diagnóstico completado em {diag_time:.2f}s")
        print(f"\nResultado:")
        print(f"  Status: {result['status']}")
        print(f"  Iluminação: {result['metrics']['illumination_label']}")
        print(f"  Luminância média: {result['metrics']['mean_luma']:.1f}/255")
        print(f"  Uniformidade: {result['metrics']['uniformity']:.1%}")
        print(f"  Diagnóstico SLM: {result['diagnosis']}")
        
        if torch.cuda.is_available():
            print(f"\n  VRAM na execução: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
        
    except Exception as e:
        print(f"❌ Erro ao executar diagnóstico: {e}")
        logger.exception("Detalhes do erro:")
        return
    
    # Resumo
    print_section("RESUMO - TESTE BEM-SUCEDIDO ✅")
    print(f"Pipeline inicializado em: {pipeline_time:.2f}s")
    print(f"Modelo carregado em: {model_time:.2f}s")
    print(f"Diagnóstico executado em: {diag_time:.2f}s")
    print(f"TEMPO TOTAL: {pipeline_time + model_time + diag_time:.2f}s")
    print(f"\nQwen está funcionando na Jetson Nano! 🚀")

if __name__ == "__main__":
    main()
