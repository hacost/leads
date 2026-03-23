import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from src.presentation.api.main import app

from src.presentation.api.auth import get_current_user

@pytest.fixture
def auth_client():
    client = TestClient(app)
    client.headers.update({"Authorization": "Bearer fake_token_tenant"})
    return client

def test_delete_category_retorna_204_con_token_valido(auth_client):
    app.dependency_overrides[get_current_user] = lambda: {"sub": "tenant_1", "role": "tenant"}
    with patch('src.presentation.api.categories.StorageService.delete_category', return_value=True):
        response = auth_client.delete("/api/categories/1")
        assert response.status_code == 204
    app.dependency_overrides.clear()

def test_delete_category_no_encontrado_retorna_404(auth_client):
    app.dependency_overrides[get_current_user] = lambda: {"sub": "tenant_1", "role": "tenant"}
    with patch('src.presentation.api.categories.StorageService.delete_category', return_value=False):
        response = auth_client.delete("/api/categories/999")
        assert response.status_code == 404
    app.dependency_overrides.clear()

def test_update_category_retorna_200_con_token_valido(auth_client):
    app.dependency_overrides[get_current_user] = lambda: {"sub": "tenant_1", "role": "tenant"}
    with patch('src.presentation.api.categories.StorageService.update_category', return_value=True):
        payload = {"name": "NuevaCategoria"}
        response = auth_client.put("/api/categories/1", json=payload)
        assert response.status_code == 200
        assert response.json()["name"] == "NuevaCategoria"
    app.dependency_overrides.clear()
