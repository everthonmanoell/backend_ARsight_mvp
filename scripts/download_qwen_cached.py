#!/usr/bin/env python3
"""
Download e cache local do modelo Qwen2.5-0.5B-Instruct
Roda aqui no Legion para pré-cachear o modelo
Depois copia para Jetson Nano para uso offline

Uso:
    python3 scripts/download_qwen_cached.py
"""

import os
from pathlib import Path

# Criar diretório de cache se não existir
CACHE_DIR = Path("./models/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Apontar para o cache
os.environ["TRANSFORMERS_CACHE"] = str(CACHE_DIR)

print("=" * 80)
print(f"📦 Downloading Qwen2.5-0.5B-Instruct to: {CACHE_DIR.absolute()}")
print("=" * 80)

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    
    print(f"\n1️⃣  Baixando tokenizer ({model_name})...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        cache_dir=str(CACHE_DIR),
    )
    print(f"   ✅ Tokenizer cached")
    
    print(f"\n2️⃣  Baixando modelo ({model_name})...")
    print("   ⏳ Isso pode levar 5-10 minutos (modelo tem ~1GB)...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        trust_remote_code=True,
        cache_dir=str(CACHE_DIR),
        torch_dtype="auto",
        device_map="cpu",  # Salvar em CPU temporariamente para download
    )
    print(f"   ✅ Modelo cached")
    
    print("\n" + "=" * 80)
    print("✅ SUCESSO! Modelo pré-cacheado e pronto para Jetson")
    print("=" * 80)
    print(f"\n📍 Cache location: {CACHE_DIR.absolute()}")
    print(f"\n💡 Para usar no Jetson:")
    print(f"   rsync -av models/cache/ jetson:~/tcc/backend_tcc_mvp/models/cache/")
    print(f"\n   Depois na Jetson:")
    print(f"   export TRANSFORMERS_CACHE=/home/das9/tcc/backend_tcc_mvp/models/cache")
    print(f"   poetry run python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000")
    
except Exception as e:
    print(f"\n❌ ERRO ao baixar modelo: {e}")
    print(f"\nDica: Verifique sua conexão com internet e espaço em disco (~2GB)")
    raise
