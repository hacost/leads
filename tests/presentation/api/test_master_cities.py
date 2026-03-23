import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from src.presentation.api.main import app
from src.presentation.api.auth import get_current_user

client = TestClient(app)

def override_get_current_user():
    return {"sub": "test_chat_123", "role": "admin"}

@pytest.fixture
def auth_client():
    client = TestClient(app)
    client.headers.update({"Authorization": "Bearer fake_token_admin"})
    return client

def test_create_master_city_con_token_valido_retorna_201(auth_client):
    payload = {"name": "Nueva York", "state": "NY", "country": "USA"}
    app.dependency_overrides[get_current_user] = lambda: {"sub": "admin_1", "role": "admin"}
    with patch('src.presentation.api.master_cities.StorageService.create_master_city') as mock_create:
        mock_create.return_value = 99
        response = auth_client.post("/api/cities", json=payload, headers={"Authorization": "Bearer fake"})
        assert response.status_code == 201
    app.dependency_overrides.clear()
    assert response.json()["id"] == 99
    assert response.json()["name"] == "Nueva York"
    assert response.json()["state"] == "NY"
    assert response.json()["country"] == "USA"

def test_create_master_city_sin_token_retorna_401():
    client = TestClient(app)
    response = client.post("/api/cities", json={"name": "Nueva York", "state": "NY", "country": "USA"})
    assert response.status_code == 401

def test_delete_city_retorna_204_con_admin(auth_client):
    app.dependency_overrides[get_current_user] = lambda: {"sub": "admin_1", "role": "admin"}
    with patch('src.presentation.api.master_cities.StorageService.delete_master_city', return_value=True):
        response = auth_client.delete("/api/cities/1")
        assert response.status_code == 204
    app.dependency_overrides.clear()

def test_delete_city_rechaza_con_403_si_no_es_admin(auth_client):
    app.dependency_overrides[get_current_user] = lambda: {"sub": "tenant_1", "role": "tenant"}
    response = auth_client.delete("/api/cities/1")
    assert response.status_code == 403
    app.dependency_overrides.clear()

def test_update_city_retorna_200_con_admin(auth_client):
    app.dependency_overrides[get_current_user] = lambda: {"sub": "admin_1", "role": "admin"}
    with patch('src.presentation.api.master_cities.StorageService.update_master_city', return_value=True):
        payload = {"name": "Leon", "state": "GTO", "country": "Mexico"}
        response = auth_client.put("/api/cities/1", json=payload)
        assert response.status_code == 200
    app.dependency_overrides.clear()
