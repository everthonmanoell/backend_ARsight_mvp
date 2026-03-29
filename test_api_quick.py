"""
Quick API Test via Terminal
Testa a API com um batch de imagens sem precisar usar /docs

Uso:
    python test_api_quick.py
    
    ou com poetry:
    poetry run python test_api_quick.py
"""
import requests
import json
import time
from pathlib import Path

# Configuração
API_URL = "http://localhost:8000/diagnose/batch"
BATCH_FOLDER = "data/uploads/20260315_143615"  # Altere conforme necessário

def test_api():
    """Testa API com um batch de imagens"""
    
    # Procura por imagens no batch
    batch_path = Path(BATCH_FOLDER)
    images = sorted(batch_path.glob("frame_*.jpg"))
    
    if not images:
        print(f"❌ Nenhuma imagem encontrada em '{BATCH_FOLDER}'")
        return
    
    print(f"📸 Encontradas {len(images)} imagens")
    
    # Prepara multipart form data
    files = []
    for img_path in images:
        with open(img_path, 'rb') as f:
            files.append(('files', (img_path.name, f.read(), 'image/jpeg')))
    
    print(f"📤 Enviando {len(files)} imagens para {API_URL}...")
    
    # Faz requisição
    t_start = time.perf_counter()
    
    try:
        response = requests.post(API_URL, files=files, timeout=60)
        t_elapsed = time.perf_counter() - t_start
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ Sucesso em {t_elapsed:.2f}s")
            print(f"\n📊 Resultados:")
            print(f"  Overall Risk: {result['summary']['overall_risk'].upper()}")
            print(f"  Dominant Label: {result['summary']['dominant_label']}")
            print(f"  Normal Frames: {result['summary']['normal_count']}/{len(files)}")
            print(f"  Problem Frames: {result['summary']['problem_count']}/{len(files)}")
            print(f"  Processing Time (API): {result['summary']['processing_time_s']:.2f}s")
            print(f"  Total Time (incl. upload): {t_elapsed:.2f}s")
            
            # Salva resultado em JSON
            output_file = Path("outputs/api_test_result.json")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"\n💾 Resultado salvo em: {output_file}")
            
        else:
            print(f"❌ Erro {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("⚠️  Certifique-se de que a API está rodando: poetry run ar-api")

if __name__ == "__main__":
    test_api()
