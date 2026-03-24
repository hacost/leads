import pytest
from fastapi.testclient import TestClient
from src.presentation.api.main import app

client = TestClient(app)

def test_health_endpoint_response():
    """
    Comprueba que al llamar a /health se obtenga un 200 OK.
    Esto garantiza que main.py ha cargado todos los routers y sys sin errores de importación.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Bastion Core API is running"}
