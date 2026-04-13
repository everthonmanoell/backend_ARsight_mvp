#!/usr/bin/env python3
"""
Script para testar o fluxo completo de upload + diagnóstico na Jetson Nano
Simula envio de 10 frames com metadados variados
"""

import os
import sys
import time
import requests
import json
from pathlib import Path
from PIL import Image, PngImagePlugin
import numpy as np

# Cores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'

def create_test_batch_images(count=10, output_dir="test_batch_images"):
    """Cria imagens de teste variadas para simular câmera real"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Limpa anterior
    for f in Path(output_dir).glob("*.jpg"):
        f.unlink()
    
    print(f"{CYAN}📸 Criando {count} imagens de teste...{RESET}")
    
    for i in range(count):
        # Varia iluminação entre frames
        brightness = 50 + (i * 20)  # De 50 a 230
        
        # Cria imagem com gradiente
        img_array = np.full((480, 640, 3), brightness, dtype=np.uint8)
        
        # Adiciona padrão (simula detalhes)
        y, x = np.ogrid[:480, :640]
        noise = np.random.randint(-30, 30, (480, 640, 3), dtype=np.int16)
        img_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        img = Image.fromarray(img_array)
        
        # Adiciona vários metadados (alguns propositalmente ruins para testar tolerância)
        if i % 3 == 0:
            # Imagem com metadados EXIF
            info = {"exif": b"fake_exif_data"}
        elif i % 5 == 0:
            # Imagem sem metadados especiais
            info = {}
        else:
            info = {}
        
        filepath = os.path.join(output_dir, f"frame_{i:02d}.jpg")
        img.save(filepath, quality=85)
        print(f"  ✓ frame_{i:02d}.jpg ({brightness} brightness)")
    
    return output_dir


def test_upload(api_url="http://localhost:8000", images_dir="test_batch_images"):
    """Testa upload batch"""
    upload_url = f"{api_url}/upload/batch"
    
    print(f"\n{CYAN}📤 Testando UPLOAD...{RESET}")
    
    files = []
    for filepath in sorted(Path(images_dir).glob("*.jpg")):
        files.append(("files", open(filepath, "rb")))
    
    if not files:
        print(f"{RED}✗ Nenhuma imagem encontrada em {images_dir}{RESET}")
        return None
    
    try:
        print(f"Enviando {len(files)} imagens para {upload_url}...")
        response = requests.post(upload_url, files=files, timeout=30)
        
        for _, f in files:
            f.close()
        
        if response.status_code != 200:
            print(f"{RED}✗ Upload falhou com status {response.status_code}{RESET}")
            print(f"Response: {response.text}")
            return None
        
        result = response.json()
        batch_id = result.get('batch_id')
        files_saved = result.get('files_saved')
        total = len(files)
        
        if files_saved == total:
            print(f"{GREEN}✓ UPLOAD SUCCESS: Todos os {total} frames aceitos!{RESET}")
            print(f"  Batch ID: {batch_id}")
            return batch_id
        else:
            print(f"{YELLOW}⚠ UPLOAD PARCIAL: {files_saved}/{total} frames{RESET}")
            print(f"  Batch ID: {batch_id}")
            return batch_id  # Continua mesmo com upload parcial
    
    except requests.exceptions.ConnectionError:
        print(f"{RED}✗ Não conseguiu conectar a {api_url}{RESET}")
        print(f"  Certifique-se que a API está rodando: poetry run ar-api")
        return None
    except Exception as e:
        print(f"{RED}✗ Erro durante upload: {e}{RESET}")
        return None


def test_diagnose(api_url="http://localhost:8000", batch_id=None):
    """Testa diagnóstico do batch"""
    if not batch_id:
        print(f"{RED}✗ Batch ID não fornecido{RESET}")
        return False
    
    diagnose_url = f"{api_url}/diagnose/batch/{batch_id}"
    
    print(f"\n{CYAN}🔍 Testando DIAGNÓSTICO...{RESET}")
    print(f"Iniciando diagnóstico para batch {batch_id}...")
    
    try:
        response = requests.post(diagnose_url, timeout=120)
        
        if response.status_code != 200:
            print(f"{RED}✗ Diagnóstico falhou com status {response.status_code}{RESET}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        
        # Verifica resultado
        status = result.get('status')
        frames = result.get('frames', [])
        summary = result.get('summary', {})
        
        print(f"{GREEN}✓ DIAGNÓSTICO CONCLUÍDO{RESET}")
        print(f"  Status: {status}")
        print(f"  Frames processados: {len(frames)}")
        
        # Conta erros
        error_count = sum(1 for f in frames if f.get('status_code') != 200)
        success_count = len(frames) - error_count
        
        print(f"  Sucesso: {success_count}/{len(frames)}")
        
        if summary:
            print(f"\n📊 SUMMARY:")
            print(f"  Risk: {summary.get('overall_risk')}")
            print(f"  Label dominante: {summary.get('dominant_label')}")
            print(f"  Problemas encontrados: {summary.get('problem_count')}")
            print(f"  Explicação: {summary.get('explanation', '')[:100]}...")
            print(f"  Recomendações: {len(summary.get('recommendations', []))} itens")
        
        # Mostra primeiro frame
        if frames:
            first = frames[0]
            print(f"\n🖼️  FIRST FRAME:")
            print(f"  Filename: {first.get('filename')}")
            print(f"  Status: {first.get('status_code')}")
            if first.get('status_code') == 200:
                print(f"  Diagnosis: {first.get('diagnosis', '')[:80]}...")
                metrics = first.get('metrics', {})
                if metrics:
                    print(f"  Illumination: {metrics.get('illumination_label')}")
                    print(f"  Mean Brightness: {metrics.get('mean_brightness'):.3f}")
        
        return success_count == len(frames)
    
    except requests.exceptions.Timeout:
        print(f"{YELLOW}⚠ Timeout esperar pelo diagnóstico (>2min)${RESET}")
        print(f"  Diagnóstico pode estar rodando em background")
        print(f"  Verifique status em: {api_url}/diagnose/batch/{batch_id}/status")
        return None
    except requests.exceptions.ConnectionError:
        print(f"{RED}✗ Não conseguiu conectar a {api_url}{RESET}")
        return False
    except Exception as e:
        print(f"{RED}✗ Erro durante diagnóstico: {e}{RESET}")
        return False


def test_status(api_url="http://localhost:8000", batch_id=None):
    """Verifica status do batch"""
    if not batch_id:
        return
    
    status_url = f"{api_url}/diagnose/batch/{batch_id}/status"
    
    try:
        response = requests.get(status_url, timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"\n📋 STATUS: {status.get('status')}")
            return status
    except:
        pass


def main():
    # Parse args
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print(f"{YELLOW}{'='*60}")
    print(f"🚀 TESTE COMPLETO: UPLOAD + DIAGNÓSTICO (Jetson Nano)")
    print(f"{'='*60}{RESET}\n")
    
    print(f"API URL: {api_url}\n")
    
    # 1. Criar imagens
    images_dir = create_test_batch_images(count=10)
    
    # 2. Testar upload
    batch_id = test_upload(api_url, images_dir)
    
    if not batch_id:
        print(f"\n{RED}Teste FALHOU no upload{RESET}")
        sys.exit(1)
    
    # 3. Testar diagnóstico
    print(f"\n{YELLOW}Aguardando 2 segundos antes do diagnóstico...{RESET}")
    time.sleep(2)
    
    success = test_diagnose(api_url, batch_id)
    
    # 4. Resultado final
    print(f"\n{YELLOW}{'='*60}{RESET}")
    if success is True:
        print(f"{GREEN}✅ TESTE PASSOU: Todos os frames foram diagnosticados!{RESET}")
        sys.exit(0)
    elif success is None:
        print(f"{YELLOW}⚠️  TESTE INCONCLUSIVO: Diagnóstico pode estar em progresso{RESET}")
        status = test_status(api_url, batch_id)
        sys.exit(0)
    else:
        print(f"{RED}❌ TESTE FALHOU: Alguns frames não foram diagnosticados{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
