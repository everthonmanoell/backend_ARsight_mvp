"""
Test API - MVP
Testa endpoints da API
uso: pytest tests/test_api.py
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from app.api.main import app
from app.api.routes import set_pipeline
from app.pipeline.illumination_pipeline import IlluminationPipeline

@pytest.fixture(scope="module")
def client():
    """Configura TestClient com pipeline inicializado"""
    # Inicializa pipeline para testes (CPU para ser mais rápido)
    pipeline = IlluminationPipeline(model_type='qwen', use_4bit=False, device='cpu')
    set_pipeline(pipeline)
    
    # Cria cliente de teste
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def test_image_path():
    """Retorna caminho para imagem de teste"""
    return Path("data/illumination/normal/normal_image1.jpg")


@pytest.fixture(scope="module")
def dark_image_path():
    """Retorna caminho para imagem escura"""
    return Path("data/illumination/dark_underexposed/dark_image1.jpg")


def test_root(client):
    """Testa endpoint root"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data


def test_health(client):
    """Testa endpoint health"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "model" in data
    assert "device" in data


def test_metrics_endpoint(client, test_image_path):
    """Testa endpoint /metrics (sem LLM)"""
    if not test_image_path.exists():
        pytest.skip(f"Test image not found: {test_image_path}")
    
    with open(test_image_path, "rb") as f:
        response = client.post(
            "/metrics",
            files={"file": (test_image_path.name, f, "image/jpeg")}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "filename" in data
    assert "metrics" in data
    assert "illumination" in data["metrics"]
    assert "illumination_label" in data["metrics"]


def test_diagnose_endpoint(client, dark_image_path):
    """Testa endpoint /diagnose (com LLM)"""
    if not dark_image_path.exists():
        pytest.skip(f"Test image not found: {dark_image_path}")
    
    with open(dark_image_path, "rb") as f:
        response = client.post(
            "/diagnose",
            files={"file": (dark_image_path.name, f, "image/jpeg")}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "risk_level" in data
    assert "explanation" in data
    assert "metrics" in data
    assert "triggered_rules" in data
    assert "recommendations" in data
    
    # Verifica que imagem escura é detectada corretamente
    assert data["status"] == "fail"
    assert data["metrics"]["illumination_label"] == "underexposed"


def test_diagnose_batch_endpoint(client, test_image_path, dark_image_path):
    """Testa endpoint /diagnose/batch"""
    if not test_image_path.exists() or not dark_image_path.exists():
        pytest.skip("Test images not found")
    
    files = [
        ("files", (test_image_path.name, open(test_image_path, "rb"), "image/jpeg")),
        ("files", (dark_image_path.name, open(dark_image_path, "rb"), "image/jpeg"))
    ]
    
    response = client.post("/diagnose/batch", files=files)
    
    # Fecha os arquivos
    for _, (_, f, _) in files:
        f.close()
    
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "successful" in data
    assert "results" in data
    assert data["total"] == 2
    assert len(data["results"]) == 2


def test_upload_endpoint(client, test_image_path):
    """Testa endpoint /upload"""
    if not test_image_path.exists():
        pytest.skip(f"Test image not found: {test_image_path}")
    
    with open(test_image_path, "rb") as f:
        response = client.post(
            "/upload",
            files={"file": (test_image_path.name, f, "image/jpeg")}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "filename" in data
    assert "saved_as" in data
    assert "path" in data


def test_invalid_file_format(client):
    """Testa envio de arquivo com formato inválido"""
    response = client.post(
        "/diagnose",
        files={"file": ("test.txt", b"not an image", "text/plain")}
    )
    
    assert response.status_code == 400
    assert "Invalid file format" in response.json()["detail"]


def test_missing_file(client):
    """Testa request sem arquivo"""
    response = client.post("/diagnose")
    
    assert response.status_code == 422  # Unprocessable Entity
