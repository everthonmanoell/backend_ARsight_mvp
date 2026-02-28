"""Teste direto do modelo sem pipeline"""
import torch, time
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

print("Carregando modelo...")
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-0.5B-Instruct",
    quantization_config=quantization_config,
    device_map="auto",
    trust_remote_code=True,
    torch_dtype=torch.float16
)

tokenizer = AutoTokenizer.from_pretrained(
    "Qwen/Qwen2.5-0.5B-Instruct",
    trust_remote_code=True
)

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print("Modelo carregado!\n")

# Prompt simples
prompt = """<|im_start|>system
You are an AR specialist analyzing illumination conditions.<|im_end|>
<|im_start|>user
Scene has adequate lighting (score: 0.734). Explain why this is good for AR.<|im_end|>
<|im_start|>assistant
"""

# Teste 5x
print("=== TESTE DE GERAÇÃO (5 runs) ===")
times = []
for i in range(5):
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    start = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=80,
            temperature=0.3,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    elapsed = time.time() - start
    times.append(elapsed)
    
    # Decodifica apenas novos tokens
    input_length = inputs['input_ids'].shape[1]
    generated_tokens = outputs[0][input_length:]
    response = tokenizer.decode(generated_tokens, skip_special_tokens=True)
    
    print(f"Run {i+1}: {elapsed:.3f}s ({len(generated_tokens)} tokens)")

avg_time = sum(times) / len(times)
print(f"\nMédia: {avg_time:.3f}s")
print(f"Resposta exemplo: {response[:100]}...")
