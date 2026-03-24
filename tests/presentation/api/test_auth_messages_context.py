import pytest
from fastapi.testclient import TestClient
from src.presentation.api.main import app

client = TestClient(app)

def test_city_creation_forbidden_message():
    """
    Simula POST sin admin. 
    Verifica que el JSON tenga el mensaje específico de 'Admin role required...'.
    En fase ROJA, este test fallará porque FastAPI devuelve el formato default.
    """
from src.presentation.api.auth import get_current_user

def test_city_creation_forbidden_message():
    """
    Simula POST sin admin. 
    Verifica que el JSON tenga el mensaje específico de 'Admin role required...'.
    """
    # Override dependency globally
    app.dependency_overrides[get_current_user] = lambda: {"uid": "123", "role": "user"}
    
    headers = {"Origin": "http://localhost:3000"}
    
    response = client.post(
        "/api/cities",
        json={"name": "Test", "state": "TS", "country": "TC"},
        headers=headers
    )
    
    # Limpiar override
    app.dependency_overrides.clear()
        
    assert response.status_code == 403
    data = response.json()
    
    # En fase ROJA, esto falla porque el campo 'error' y 'code' no existen en el default de FastAPI
    # El default de FastAPI es {"detail": "..."}
    assert "error" in data
    assert data["error"] == "Forbidden"
    assert "Admin role required" in data["message"]
    assert data["code"] == "AUTH_ERROR"

def test_city_update_forbidden_message():
    """
    Simula PUT sin admin.
    Verifica que el mensaje sea 'Only admins can modify...'.
    """
    app.dependency_overrides[get_current_user] = lambda: {"uid": "123", "role": "user"}
    headers = {"Origin": "http://localhost:3000"}
    
    response = client.put(
        "/api/cities/1",
        json={"name": "Test", "state": "TS", "country": "TC"},
        headers=headers
    )
    app.dependency_overrides.clear()
        
    assert response.status_code == 403
    data = response.json()
    
    assert "error" in data
    assert "Only admins can modify" in data["message"]
    assert data["code"] == "AUTH_ERROR"
