"""
Teste rápido do warm-up da API

Simula o comportamento de startup da API para validar:
1. Carregamento de pesos
2. Warm-up automático  
3. Compilação (se habilitado)
4. Tempo total até API estar pronta
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.config import Config
from app.pipeline.illumination_pipeline import IlluminationPipeline
from PIL import Image
import numpy as np

def test_warmup(enable_compile: bool = False):
    """Testa warm-up similar ao que acontece na API"""
    
    print("="*70)
    print(f"🧪 Testando API Startup (compile={enable_compile})")
    print("="*70)
    
    # 1. Carregar config
    print("\n📋 Loading configuration...")
    config = Config()
    model_type = config.get('models.default', 'qwen')
    use_4bit = config.get('models.use_4bit', True)
    device = config.get('models.device', 'cuda')
    
    print(f"   Model: {model_type}")
    print(f"   4-bit: {use_4bit}")
    print(f"   Device: {device}")
    print(f"   Compile: {enable_compile}")
    
    # 2. Inicializar pipeline
    print(f"\n📦 Initializing pipeline...")
    if enable_compile:
        print("   ⚠️  torch.compile() ENABLED - This will take 2-5 minutes...")
    
    start_total = time.time()
    
    pipeline = IlluminationPipeline(
        model_type=model_type,
        use_4bit=use_4bit,
        device=device,
        enable_compile=enable_compile
    )
    
    init_time = time.time() - start_total
    print(f"   ✅ Pipeline initialized ({init_time:.1f}s)")
    
    # 3. Warm-up (similar ao da API)
    print(f"\n🔥 Starting warm-up...")
    start_warmup = time.time()
    
    # Criar imagem dummy
    dummy_image = Image.fromarray(
        np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
    )
    
    # Primeira inferência (carrega pesos + compila)
    print("   📸 Running dummy inference...")
    result = pipeline.diagnose(dummy_image)
    
    warmup_time = time.time() - start_warmup
    total_time = time.time() - start_total
    
    if enable_compile:
        print(f"   ✅ Warm-up complete! Model compiled and ready ({warmup_time:.1f}s)")
    else:
        print(f"   ✅ Warm-up complete! Model loaded and ready ({warmup_time:.1f}s)")
    
    print(f"\n🚀 API ready to accept requests!")
    print(f"   Total startup time: {total_time:.1f}s")
    
    # 4. Validar que próximas inferências são rápidas
    print(f"\n⚡ Testing subsequent inference speed...")
    
    # Segunda inferência
    start_second = time.time()
    result2 = pipeline.diagnose(dummy_image)
    second_time = time.time() - start_second
    
    print(f"   2ª inferência: {second_time:.2f}s")
    
    # Terceira inferência
    start_third = time.time()
    result3 = pipeline.diagnose(dummy_image)
    third_time = time.time() - start_third
    
    print(f"   3ª inferência: {third_time:.2f}s")
    
    avg_inference = (second_time + third_time) / 2
    print(f"   Média: {avg_inference:.2f}s/imagem")
    
    # 5. Resumo
    print(f"\n{'='*70}")
    print(f"📊 RESUMO")
    print(f"{'='*70}")
    print(f"⏱️  Startup total: {total_time:.1f}s")
    print(f"   - Inicialização: {init_time:.1f}s")
    print(f"   - Warm-up (1ª inferência): {warmup_time:.1f}s")
    print(f"")
    print(f"⚡ Performance:")
    print(f"   - 2ª+ inferências: {avg_inference:.2f}s/imagem")
    
    if enable_compile:
        improvement = ((warmup_time - avg_inference) / warmup_time) * 100
        print(f"   - Speedup após compile: {improvement:.1f}% mais rápido")
    
    print(f"{'='*70}")
    print(f"💡 CONCLUSÃO:")
    if enable_compile:
        print(f"   Com torch.compile(), startup é lento ({total_time:.1f}s)")
        print(f"   MAS todas inferências ficam {improvement:.1f}% mais rápidas!")
        print(f"   Recomendado para: Produção de longa duração")
    else:
        print(f"   Sem compile, startup é rápido ({total_time:.1f}s)")
        print(f"   Performance já é ótima com TRUE BATCH!")
        print(f"   Recomendado para: Desenvolvimento e deploy normal")
    print(f"{'='*70}")

def main():
    """Testa ambas configurações"""
    
    print("\n" + "="*70)
    print("🚀 API STARTUP WARM-UP TEST")
    print("="*70)
    
    # Teste 1: Sem compile (padrão)
    test_warmup(enable_compile=False)
    
    # Opcionalmente testar com compile (demora muito!)
    print("\n\n")
    response = input("⚠️  Quer testar COM torch.compile()? (demora 2-5min) [s/N]: ")
    
    if response.lower() == 's':
        print("\n")
        test_warmup(enable_compile=True)
    else:
        print("\n⏭️  Pulando teste com compile (muito demorado)")
        print("\nPara testar compile posteriormente:")
        print("  python tests/test_api_warmup.py")
        print("  e responda 's' quando perguntado")

if __name__ == "__main__":
    main()
