#!/usr/bin/env python3
"""
Teste rápido na Jetson Nano com os ajustes atuais
Mede tempo, detecção de junk, e qualidade de resposta
"""

import os
import sys
import time
import requests
import json
from pathlib import Path

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'

def test_nano_performance(api_url="http://localhost:8000"):
    """Teste rápido com 5 imagens"""
    
    print(f"{CYAN}{'='*60}")
    print(f"🧪 TESTE NANO - Diagnóstico Rápido (5 frames)")
    print(f"{'='*60}{RESET}\n")
    
    # 1. Criar 5 imagens mínimas
    print(f"{YELLOW}1. Criando 5 imagens de teste...{RESET}")
    import numpy as np
    from PIL import Image
    
    test_dir = "test_quick"
    os.makedirs(test_dir, exist_ok=True)
    
    for i in range(5):
        brightness = 50 + (i * 40)  # 50, 90, 130, 170, 210
        img_array = np.full((480, 640, 3), brightness, dtype=np.uint8)
        img = Image.fromarray(img_array)
        img.save(os.path.join(test_dir, f"img_{i}.jpg"))
        print(f"  ✓ img_{i}.jpg (brightness {brightness})")
    
    # 2. Upload
    print(f"\n{YELLOW}2. Fazendo upload...{RESET}")
    files = [("files", open(os.path.join(test_dir, f"img_{i}.jpg"), "rb")) for i in range(5)]
    response = requests.post(f"{api_url}/upload/batch", files=files, timeout=30)
    for _, f in files:
        f.close()
    
    if response.status_code != 200:
        print(f"{RED}✗ Upload falhou: {response.status_code}{RESET}")
        return
    
    batch_id = response.json().get('batch_id')
    print(f"  ✓ Batch ID: {batch_id}")
    
    # 3. Diagnóstico com cronômetro
    print(f"\n{YELLOW}3. Executando diagnóstico...{RESET}")
    t_start = time.time()
    response = requests.post(f"{api_url}/diagnose/batch/{batch_id}", timeout=120)
    t_total = time.time() - t_start
    
    if response.status_code != 200:
        print(f"{RED}✗ Diagnóstico falhou: {response.status_code}{RESET}")
        return
    
    result = response.json()
    
    # 4. Análise de resultados
    print(f"\n{CYAN}📊 RESULTADOS:{RESET}\n")
    
    perf = result.get('performance', {})
    frames = result.get('frames', [])
    summary = result.get('summary', {})
    
    print(f"⏱️  Performance:")
    print(f"  PDI:        {perf.get('pdi_total_ms', 0):.1f}ms")
    print(f"  SLM:        {perf.get('slm_total_s', 0):.2f}s")
    print(f"  Total:      {perf.get('total_s', 0):.2f}s (esperado: ~3-4s)")
    print(f"  Target met: {perf.get('target_met', False)}")
    
    print(f"\n📈 Frames:")
    print(f"  Total: {len(frames)}")
    
    junk_count = 0
    empty_count = 0
    
    for i, frame in enumerate(frames):
        explanation = frame.get('explanation', '')
        status = frame.get('status', 'unknown')
        
        # Detecção de junk
        junk_indicators = ["I.", "edit", "formatting", "1,2,", "Lightpassing"]
        has_junk = any(ind in explanation for ind in junk_indicators)
        
        if has_junk:
            print(f"  [{i}] ⚠️  JUNK: {explanation[:50]}...")
            junk_count += 1
        elif len(explanation) < 5:
            print(f"  [{i}] 🔄 FALLBACK (template)")
            empty_count += 1
        else:
            marker = "✅" if status == "pass" else "❌"
            print(f"  [{i}] {marker} {explanation[:60]}...")
    
    print(f"\n🎯 Summary:")
    print(f"  Risk:     {summary.get('overall_risk')}")
    print(f"  Label:    {summary.get('dominant_label')}")
    print(f"  Problems: {summary.get('problem_count')}/{len(frames)}")
    
    # 5. Resultado final
    print(f"\n{CYAN}{'='*60}")
    print(f"📋 VALIDAÇÃO:{RESET}")
    print(f"  Tempo < 4.5s:        {'✅' if perf.get('total_s', 999) < 4.5 else '❌'}")
    print(f"  Sem junk (<1):       {'✅' if junk_count == 0 else f'❌ ({junk_count})'}")
    print(f"  Explicações naturais: {'✅' if junk_count == 0 else '❌'}")
    print(f"  Fallback ~20-30%:    {'✅' if 0 <= empty_count <= 2 else '⚠️'}")
    
    if perf.get('total_s', 999) < 4.5 and junk_count == 0:
        print(f"\n{GREEN}✅ TESTE PASSOU!{RESET}")
    else:
        print(f"\n{RED}❌ Ajustes ainda necessários{RESET}")

if __name__ == "__main__":
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    try:
        test_nano_performance(api_url)
    except Exception as e:
        print(f"{RED}Erro: {e}{RESET}")
        print(f"Certifique-se que a API está rodando em {api_url}")
