"""
Test API - MVP
Testa endpoints da API
"""

import pytest
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)


def test_root():
    """Testa endpoint root"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health():
    """Testa endpoint health"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
