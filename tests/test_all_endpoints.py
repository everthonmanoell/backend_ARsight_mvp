"""
Example: Using All MVP Endpoints
Demonstra uso de todos os endpoints da API
"""

import requests
from pathlib import Path
import json

# API base URL
API_URL = "http://localhost:8000"


def test_health():
    """Testa health check"""
    print("=" * 80)
    print("1. HEALTH CHECK")
    print("=" * 80)
    
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_extract_metrics():
    """Testa extração de métricas (sem LLM)"""
    print("=" * 80)
    print("2. EXTRACT METRICS ONLY (No LLM - Fast)")
    print("=" * 80)
    
    image_path = "data/illumination/adequate/normal_image1.jpg"
    
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return
    
    with open(image_path, "rb") as f:
        response = requests.post(
            f"{API_URL}/metrics",
            files={"file": f}
        )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Filename: {data['filename']}")
        print(f"Illumination: {data['metrics']['illumination']:.2f}")
        print(f"Label: {data['metrics']['illumination_label']}")
        print(f"Mean Luma: {data['metrics']['mean_luma']:.1f}")
        print(f"Uniformity: {data['metrics']['uniformity']:.2f}")
    else:
        print(f"Error: {response.text}")
    print()


def test_diagnose():
    """Testa diagnóstico completo (com LLM)"""
    print("=" * 80)
    print("3. FULL DIAGNOSIS (With LLM - Slow)")
    print("=" * 80)
    
    image_path = "data/illumination/underexposed/dark_image1.jpg"
    
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return
    
    with open(image_path, "rb") as f:
        response = requests.post(
            f"{API_URL}/diagnose",
            files={"file": f}
        )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Filename: {data['filename']}")
        print(f"Status: {data['status'].upper()}")
        print(f"Risk Level: {data['risk_level']}")
        print(f"Illumination: {data['metrics']['illumination']:.2f}")
        print(f"Explanation: {data['explanation'][:100]}...")
        if data.get('triggered_rules'):
            print(f"Issues: {', '.join(data['triggered_rules'])}")
    else:
        print(f"Error: {response.text}")
    print()


def test_upload():
    """Testa upload de imagem"""
    print("=" * 80)
    print("4. UPLOAD IMAGE (Save to disk)")
    print("=" * 80)
    
    image_path = "data/illumination/overexposed/bright_image1.jpg"
    
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return
    
    with open(image_path, "rb") as f:
        response = requests.post(
            f"{API_URL}/upload",
            files={"file": f}
        )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Original: {data['filename']}")
        print(f"Saved as: {data['saved_as']}")
        print(f"Path: {data['path']}")
        print(f"Size: {data['size_bytes']} bytes")
        print(f"Dimensions: {data['image_size']}")
    else:
        print(f"Error: {response.text}")
    print()


def test_batch_diagnose():
    """Testa diagnóstico em batch"""
    print("=" * 80)
    print("5. BATCH DIAGNOSIS")
    print("=" * 80)
    
    image_paths = [
        "data/illumination/underexposed/dark_image1.jpg",
        "data/illumination/adequate/normal_image1.jpg",
        "data/illumination/overexposed/bright_image1.jpg"
    ]
    
    # Filtra apenas imagens que existem
    existing_paths = [p for p in image_paths if Path(p).exists()]
    
    if not existing_paths:
        print("❌ No images found")
        return
    
    files = [("files", open(p, "rb")) for p in existing_paths]
    
    try:
        response = requests.post(
            f"{API_URL}/diagnose/batch",
            files=files
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total: {data['total']}")
            print(f"Successful: {data['successful']}")
            print(f"Failed: {data['failed']}")
            print("\nResults:")
            for result in data['results']:
                if result.get('status_code', 200) == 200:
                    print(f"  ✓ {result['filename']}")
                    print(f"    Status: {result['status'].upper()}")
                    print(f"    Illumination: {result['metrics']['illumination_label']}")
                else:
                    print(f"  ✗ {result['filename']}: {result.get('error', 'Unknown error')}")
        else:
            print(f"Error: {response.text}")
    finally:
        # Fecha todos os arquivos
        for _, f in files:
            f.close()
    
    print()


def test_batch_upload():
    """Testa upload em batch"""
    print("=" * 80)
    print("6. BATCH UPLOAD")
    print("=" * 80)
    
    image_paths = [
        "data/illumination/adequate/normal_image1.jpg",
        "data/illumination/adequate/normal_image2.jpg"
    ]
    
    # Filtra apenas imagens que existem
    existing_paths = [p for p in image_paths if Path(p).exists()]
    
    if not existing_paths:
        print("❌ No images found")
        return
    
    files = [("files", open(p, "rb")) for p in existing_paths]
    
    try:
        response = requests.post(
            f"{API_URL}/upload/batch",
            files=files
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total: {data['total']}")
            print(f"Successful: {data['successful']}")
            print(f"Failed: {data['failed']}")
            print("\nResults:")
            for result in data['results']:
                if result.get('status') == 'success':
                    print(f"  ✓ {result['filename']} → {result['saved_as']}")
                else:
                    print(f"  ✗ {result['filename']}: {result.get('error', 'Unknown error')}")
        else:
            print(f"Error: {response.text}")
    finally:
        # Fecha todos os arquivos
        for _, f in files:
            f.close()
    
    print()


if __name__ == "__main__":
    print("\n🚀 AR DIAGNOSTIC MVP - API ENDPOINTS TEST\n")
    
    try:
        test_health()
        test_extract_metrics()
        test_diagnose()
        test_upload()
        test_batch_diagnose()
        test_batch_upload()
        
        print("=" * 80)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 80)
        print("\nEndpoints available:")
        print("  - GET  /health           - Health check")
        print("  - POST /metrics          - Extract metrics only (fast)")
        print("  - POST /diagnose         - Full diagnosis with LLM")
        print("  - POST /diagnose/batch   - Batch diagnosis")
        print("  - POST /upload           - Upload and save image")
        print("  - POST /upload/batch     - Batch upload")
        print("  - GET  /docs             - Interactive API docs (Swagger)")
        print("\n")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API")
        print("   Make sure the API is running: poetry run ar-api")
    except Exception as e:
        print(f"❌ Error: {e}")
