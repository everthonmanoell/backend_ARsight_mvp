"""
Test API - MVP
Testa os endpoints /diagnose/batch e /upload/batch
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
    """Configura TestClient com pipeline inicializado (CPU para CI rápido)"""
    pipeline = IlluminationPipeline(model_type='qwen', use_4bit=False, device='cpu')
    set_pipeline(pipeline)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def normal_image_path():
    return Path("data/illumination/normal/normal_image1.jpg")


@pytest.fixture(scope="module")
def dark_image_path():
    return Path("data/illumination/dark_underexposed/dark_image1.jpg")


@pytest.fixture(scope="module")
def bright_image_path():
    return Path("data/illumination/bright_overexposed/bright_image1.jpg")



# ──────────────────────────────────────────────────────────────────────────────
# Testes de infraestrutura
# ──────────────────────────────────────────────────────────────────────────────

def test_root(client):
    """GET / — lista os endpoints disponíveis"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "endpoints" in data
    assert "diagnose_batch" in data["endpoints"]
    assert "upload_batch" in data["endpoints"]


def test_health(client):
    """GET /health — confirma que pipeline está carregado"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model" in data
    assert "device" in data


# ──────────────────────────────────────────────────────────────────────────────
# Testes do endpoint principal: POST /diagnose/batch
# ──────────────────────────────────────────────────────────────────────────────

def test_diagnose_batch_mixed(client, normal_image_path, dark_image_path):
    """Batch com imagem normal + imagem escura — verifica estrutura summary+frames"""
    if not normal_image_path.exists() or not dark_image_path.exists():
        pytest.skip("Imagens de teste nao encontradas")

    files = [
        ("files", (normal_image_path.name, open(normal_image_path, "rb"), "image/jpeg")),
        ("files", (dark_image_path.name,   open(dark_image_path,   "rb"), "image/jpeg")),
    ]
    response = client.post("/diagnose/batch", files=files)
    for _, (_, f, _) in files:
        f.close()

    assert response.status_code == 200
    data = response.json()

    # Estrutura de topo
    assert "summary" in data
    assert "frames" in data
    assert len(data["frames"]) == 2

    # Summary
    s = data["summary"]
    for field in ("overall_risk", "dominant_label", "problem_count", "normal_count",
                  "explanation", "recommendations", "metrics_avg", "processing_time_s"):
        assert field in s, f"Campo '{field}' ausente no summary"
    assert s["problem_count"] + s["normal_count"] == 2

    # Estrutura de cada frame
    for item in data["frames"]:
        assert "filename" in item
        assert "status" in item
        assert "risk_level" in item
        assert "explanation" in item
        assert "triggered_rules" in item
        assert "recommendations" in item
        assert "frame_index" in item
        # Metricas PDI completas
        m = item["metrics"]
        for field in ("illumination_score", "illumination_label", "mean_brightness",
                      "mean_luma", "std_luma", "uniformity",
                      "pct_clipped_dark", "pct_clipped_bright"):
            assert field in m, f"Campo '{field}' ausente nas metricas"

    # Verifica deteccao correta da imagem escura
    dark_frame = next(r for r in data["frames"] if r["filename"] == dark_image_path.name)
    assert dark_frame["status"] == "fail"
    assert dark_frame["metrics"]["illumination_label"] == "underexposed"


def test_diagnose_batch_three_categories(client, normal_image_path, dark_image_path, bright_image_path):
    """Batch com 3 categorias diferentes — verifica detecção de cada classe"""
    paths = [normal_image_path, dark_image_path, bright_image_path]
    if not all(p.exists() for p in paths):
        pytest.skip("Imagens de teste não encontradas")

    files = [("files", (p.name, open(p, "rb"), "image/jpeg")) for p in paths]
    response = client.post("/diagnose/batch", files=files)
    for _, (_, f, _) in files:
        f.close()

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "frames" in data
    assert len(data["frames"]) == 3

    labels = {r["filename"]: r["metrics"]["illumination_label"] for r in data["frames"]}
    assert labels[dark_image_path.name]   == "underexposed"
    assert labels[bright_image_path.name] == "overexposed"


def test_diagnose_batch_too_many_files(client, normal_image_path):
    """Batch com mais de 10 arquivos deve retornar 400"""
    if not normal_image_path.exists():
        pytest.skip("Imagem de teste não encontrada")

    files = [("files", (f"img{i}.jpg", open(normal_image_path, "rb"), "image/jpeg"))
             for i in range(11)]
    response = client.post("/diagnose/batch", files=files)
    for _, (_, f, _) in files:
        f.close()

    assert response.status_code == 400
    assert "Max batch size" in response.json()["detail"]


def test_diagnose_batch_invalid_format(client):
    """Arquivo com formato invalido no batch deve retornar frame com erro"""
    response = client.post(
        "/diagnose/batch",
        files={"files": ("test.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    error_frames = [f for f in data["frames"] if f.get("status_code", 200) != 200]
    assert len(error_frames) >= 1


# ──────────────────────────────────────────────────────────────────────────────
# Testes do endpoint POST /upload/batch
# ──────────────────────────────────────────────────────────────────────────────

def test_upload_batch(client, normal_image_path, dark_image_path):
    """Upload de 2 imagens — verifica salvamento em disco"""
    if not normal_image_path.exists() or not dark_image_path.exists():
        pytest.skip("Imagens de teste não encontradas")

    files = [
        ("files", (normal_image_path.name, open(normal_image_path, "rb"), "image/jpeg")),
        ("files", (dark_image_path.name,   open(dark_image_path,   "rb"), "image/jpeg")),
    ]
    response = client.post("/upload/batch", files=files)
    for _, (_, f, _) in files:
        f.close()

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["successful"] == 2
    for item in data["results"]:
        assert item["status"] == "success"
        assert "saved_as" in item
        assert "path" in item



