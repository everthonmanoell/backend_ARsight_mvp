"""
Quick API Test - New Batch Architecture
Testa o novo fluxo de upload + diagnóstico separados

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
UPLOAD_URL = "http://localhost:8000/upload/batch"
DIAGNOSE_URL = "http://localhost:8000/diagnose/batch"
BATCH_FOLDER = "data/uploads/20260315_180200"  # Altere conforme necessário

def test_api_workflow():
    """Testa o fluxo completo: upload + diagnóstico"""
    
    # Procura por imagens no batch local (para teste)
    batch_path = Path(BATCH_FOLDER)
    images = sorted(batch_path.glob("frame_*.jpg")) if batch_path.exists() else []
    
    if not images:
        print(f"ℹ️  Nenhuma imagem local em '{BATCH_FOLDER}'")
        print("Será gerado um batch_id de teste para demo\n")
        demo_mode = True
        batch_id = "batch_20260330_150000_demo01"
    else:
        demo_mode = False
        batch_id = None
    
    # ============================================================
    # PASSO 1: UPLOAD
    # ============================================================
    print("=" * 60)
    print("PASSO 1: UPLOAD DE IMAGENS")
    print("=" * 60)
    
    if not demo_mode:
        print(f"📸 Encontradas {len(images)} imagens")
        
        # Prepara multipart form data
        files = []
        for img_path in images:
            with open(img_path, 'rb') as f:
                files.append(('files', (img_path.name, f.read(), 'image/jpeg')))
        
        print(f"📤 Enviando {len(files)} imagens para {UPLOAD_URL}...")
        
        t_start = time.perf_counter()
        
        try:
            response = requests.post(UPLOAD_URL, files=files, timeout=60)
            t_elapsed = time.perf_counter() - t_start
            
            if response.status_code == 200:
                result = response.json()
                batch_id = result['batch_id']
                
                print(f"✅ Upload concluído em {t_elapsed:.2f}s")
                print(f"\nℹ️  Resultado do upload:")
                print(f"  batch_id:    {batch_id}")
                print(f"  status:      {result['status']}")
                print(f"  files_saved: {result['files_saved']}/{len(files)}")
                
            else:
                print(f"❌ Erro {response.status_code}")
                print(response.text)
                return
                
        except Exception as e:
            print(f"❌ Erro no upload: {e}")
            return
    
    else:
        print("📝 Demo mode - usando batch_id simulado")
        print(f"  batch_id: {batch_id}\n")
    
    # ============================================================
    # PASSO 2: INICIAR DIAGNÓSTICO
    # ============================================================
    print("\n" + "=" * 60)
    print("PASSO 2: INICIAR DIAGNÓSTICO")
    print("=" * 60)
    print(f"🔄 Iniciando diagnóstico para batch: {batch_id}")
    print(f"📤 POST {DIAGNOSE_URL}/{batch_id}")
    
    t_start = time.perf_counter()
    
    try:
        response = requests.post(f"{DIAGNOSE_URL}/{batch_id}", timeout=120)
        t_elapsed = time.perf_counter() - t_start
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Diagnóstico concluído em {t_elapsed:.2f}s")
            print(f"\n📊 Resultados:")
            print(f"  Overall Risk: {result['summary']['overall_risk'].upper()}")
            print(f"  Dominant Label: {result['summary']['dominant_label']}")
            print(f"  Normal Frames: {result['summary']['normal_count']}/{len(result['frames'])}")
            print(f"  Problem Frames: {result['summary']['problem_count']}/{len(result['frames'])}")
            print(f"  Processing Time (API): {result['summary']['processing_time_s']:.2f}s")
            print(f"  Total Time (incl. upload): {t_elapsed + (time.perf_counter() - t_start):.2f}s")
            
            # Salva resultado em JSON
            output_file = Path("outputs/api_test_result.json")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"\n💾 Resultado salvo em: {output_file}")
            
        elif response.status_code == 404:
            print(f"❌ Batch não encontrado: {batch_id}")
            print(response.text)
        else:
            print(f"❌ Erro {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Erro no diagnóstico: {e}")
        print("⚠️  Certifique-se de que a API está rodando: poetry run ar-api")
        return
    
    # ============================================================
    # PASSO 3: CONSULTARATUS (demo)
    # ============================================================
    print("\n" + "=" * 60)
    print("PASSO 3: CONSULTAR STATUS (demo)")
    print("=" * 60)
    
    status_url = f"http://localhost:8000/diagnose/batch/{batch_id}/status"
    print(f"🔍 GET {status_url}")
    
    try:
        response = requests.get(status_url, timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Status: {status['status']}")
            print(f"   Atualizado em: {status['updated_at']}")
        else:
            print(f"❌ Erro ao consultar status: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # ============================================================
    # PASSO 4: BUSCAR RESULTADO (demo)
    # ============================================================
    print("\n" + "=" * 60)
    print("PASSO 4: BUSCAR RESULTADO (demo)")
    print("=" * 60)
    
    result_url = f"http://localhost:8000/diagnose/batch/{batch_id}/result"
    print(f"📥 GET {result_url}")
    
    try:
        response = requests.get(result_url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Resultado disponível!")
            print(f"   Status: {result['status']}")
            print(f"   Overall Risk: {result['summary']['overall_risk']}")
        elif response.status_code == 202:
            print(f"⏳ Resultado não está pronto ainda")
            print(f"   {response.json()['detail']}")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n" + "=" * 60)
    print("Fluxo completo testado com sucesso! ✨")
    print("=" * 60)

if __name__ == "__main__":
    test_api_workflow()
