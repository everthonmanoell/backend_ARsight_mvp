#!/usr/bin/env python3
"""
Script de teste para validar o fix da rota de upload na Jetson Nano
Testa validação de imagens com metadados EXIF corrompidos
"""

import os
import sys
import requests
import json
from pathlib import Path
from PIL import Image
import numpy as np

# Cores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def create_test_images(count=5, output_dir="test_images"):
    """Cria imagens de teste com potenciais issues EXIF"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Apaga conteúdo anterior
    for f in Path(output_dir).glob("*.jpg"):
        f.unlink()
    
    for i in range(count):
        # Cria imagem aleatória
        img_array = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        
        # Salva com nome padrão
        filepath = os.path.join(output_dir, f"test_frame_{i:02d}.jpg")
        img.save(filepath)
        print(f"✓ Created {filepath}")
    
    return output_dir


def test_api_upload(api_url="http://localhost:8000", images_dir="test_images"):
    """Testa upload batch via API"""
    
    upload_url = f"{api_url}/upload/batch"
    
    # Coleta arquivos
    files = []
    for filepath in sorted(Path(images_dir).glob("*.jpg")):
        files.append(("files", open(filepath, "rb")))
    
    if not files:
        print(f"{RED}✗ No image files found in {images_dir}{RESET}")
        return False
    
    try:
        print(f"\nTesting upload to {upload_url}...")
        print(f"Uploading {len(files)} images...")
        
        response = requests.post(upload_url, files=files)
        
        # Fecha todos os arquivos
        for _, f in files:
            f.close()
        
        if response.status_code != 200:
            print(f"{RED}✗ Upload failed with status {response.status_code}{RESET}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        files_saved = result.get('files_saved', 0)
        total_files = len(files)
        
        if files_saved == total_files:
            print(f"{GREEN}✓ All {total_files} files uploaded successfully!{RESET}")
            print(f"  Batch ID: {result.get('batch_id')}")
            return True
        else:
            print(f"{YELLOW}⚠ Partial upload: {files_saved}/{total_files} files accepted{RESET}")
            print(f"  Batch ID: {result.get('batch_id')}")
            # Mostra detalhes dos erros
            for r in result.get('results', []):
                if r.get('status') == 'error':
                    print(f"  {RED}✗ {r.get('filename')}: {r.get('error')}{RESET}")
            return files_saved == total_files
    
    except requests.exceptions.ConnectionError:
        print(f"{RED}✗ Could not connect to {api_url}{RESET}")
        print(f"  Make sure API is running: poetry run ar-api")
        return False
    except Exception as e:
        print(f"{RED}✗ Error during upload: {e}{RESET}")
        return False


def main():
    # Parse args
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print(f"{YELLOW}=== Jetson Nano Upload Fix Test ==={RESET}")
    
    # 1. Cria imagens de teste
    print("\n1. Creating test images...")
    images_dir = create_test_images(count=10)
    
    # 2. Testa upload
    print("\n2. Testing API upload...")
    success = test_api_upload(api_url, images_dir)
    
    # 3. Resultado
    print("\n" + ("="*50))
    if success:
        print(f"{GREEN}✓ TEST PASSED: All images were accepted!{RESET}")
        sys.exit(0)
    else:
        print(f"{RED}✗ TEST FAILED: Some images were rejected{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
