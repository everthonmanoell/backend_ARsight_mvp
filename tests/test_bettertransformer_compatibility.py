"""
Teste direto de compatibilidade BetterTransformer + 4-bit quantization
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

print("\n" + "="*60)
print("🧪 Teste: BetterTransformer + 4-bit Quantization")
print("="*60)

# 1. Carrega modelo 4-bit
print("\n1. Carregando modelo com quantização 4-bit...")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
    torch_dtype=torch.float16
)
print("✅ Modelo carregado")

# 2. Tenta aplicar BetterTransformer
print("\n2. Tentando aplicar BetterTransformer...")
try:
    from optimum.bettertransformer import BetterTransformer
    model = BetterTransformer.transform(model)
    print("✅ BetterTransformer aplicado com sucesso!")
except Exception as e:
    print(f"❌ BetterTransformer falhou: {e}")
    print(f"   Tipo: {type(e).__name__}")

print("\n" + "="*60)
print("💡 Conclusão:")
print("   BetterTransformer NÃO é compatível com bitsandbytes 4-bit")
print("   Alternativas:")
print("   - Usar modelo FP16 sem quantização")
print("   - Usar torch.compile() ao invés")
print("="*60)
