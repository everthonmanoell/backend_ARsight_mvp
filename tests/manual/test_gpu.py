"""
GPU Diagnostic Test
Verifica disponibilidade e configuração de CUDA/GPU

uso: python tests/manual/test_gpu.py

para ativar ambiente virtual no Windows: .venv\Scripts\activate

para ativar ambiente virtual no Linux/Mac: 
# Option 1: Usar Poetry (automático)
poetry run python tests/manual/test_gpu.py

# Option 2: Se preferir ativar manualmente
source $(poetry env info --path)/bin/activate
python tests/manual/test_gpu.py 
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

print("="*70)
print("GPU DIAGNOSTIC TEST")
print("="*70)

# Test 1: PyTorch
print("\n[1/5] PyTorch CUDA availability...")
try:
    import torch
    print(f"  PyTorch version: {torch.__version__}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"  CUDA version: {torch.version.cuda}")
        print(f"  GPU count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
            print(f"    Memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")
    else:
        print("  ⚠️ CUDA not available in PyTorch")
        print(f"  PyTorch was built with CUDA: {torch.version.cuda is not None}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 2: Transformers device
print("\n[2/5] Transformers device detection...")
try:
    from transformers import AutoModel
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Default device: {device}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 3: BitsAndBytes (for 4-bit quantization)
print("\n[3/5] BitsAndBytes availability...")
try:
    import bitsandbytes as bnb
    print(f"  BitsAndBytes version: {bnb.__version__}")
    print(f"  ✅ BitsAndBytes installed")
except Exception as e:
    print(f"  ❌ BitsAndBytes not available: {e}")

# Test 4: Simple tensor test
print("\n[4/5] Testing CUDA tensor operations...")
try:
    import torch
    if torch.cuda.is_available():
        x = torch.tensor([1.0, 2.0, 3.0]).cuda()
        y = x * 2
        print(f"  ✅ CUDA tensor test successful: {y.cpu().numpy()}")
    else:
        print("  ⚠️ CUDA not available, skipping tensor test")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test 5: Config
print("\n[5/5] Checking app config...")
try:
    from app.config import Config
    config = Config()
    models_config = config.get('models', {})
    print(f"  Config device: {models_config.get('device', 'not set')}")
    print(f"  Config use_4bit: {models_config.get('use_4bit', 'not set')}")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)

# Recommendations
print("\n📋 RECOMMENDATIONS:")
import torch
if not torch.cuda.is_available():
    print("  ⚠️ CUDA not available. Possible causes:")
    print("     1. PyTorch was installed without CUDA support")
    print("     2. NVIDIA drivers are not installed")
    print("     3. CUDA toolkit is not installed")
    print("\n  To fix:")
    print("     pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
else:
    print("  ✅ CUDA is working properly")
    print(f"     GPU: {torch.cuda.get_device_name(0)}")
    print(f"     Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")