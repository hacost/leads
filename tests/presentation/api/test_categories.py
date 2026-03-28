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

def test_get_categories_retorna_200_y_master_categories(auth_client):
    app.dependency_overrides[get_current_user] = lambda: {"sub": "tenant_1", "role": "tenant"}
    mock_data = [{"id": 1, "name": "Fumigaciones", "status": 1}]
    # El nuevo método ya NO recibe owner_id
    with patch('src.presentation.api.categories.StorageService.get_categories', return_value=mock_data) as mock_get:
        response = auth_client.get("/api/categories")
        assert response.status_code == 200
        assert mock_get.call_count == 1
        # Aseguramos que fue llamado sin owner_id o bien, que en el JSON de respuesta falta owner_id
        data = response.json()
        assert len(data) == 1
        assert "owner_id" not in data[0]
    app.dependency_overrides.clear()

def test_post_category_retorna_200_al_crear_master(auth_client):
    app.dependency_overrides[get_current_user] = lambda: {"sub": "tenant_1", "role": "tenant"}
    # El método create no pasará owner_id al storage
    with patch('src.presentation.api.categories.StorageService.create_category', return_value=55) as mock_create:
        response = auth_client.post("/api/categories", json={"name": "Plomería"})
        assert response.status_code == 200
        assert response.json()["id"] == 55
        # Verificamos que se llamó sin owner_id (o sea, por defecto el nuevo master lo omite)
        mock_create.assert_called_once_with(name="Plomería")
    app.dependency_overrides.clear()

def test_delete_master_category_retorna_403_prohibido(auth_client):
    """Prueba que un inquilino no puede borrar una Master Category global."""
    app.dependency_overrides[get_current_user] = lambda: {"sub": "tenant_1", "role": "tenant"}
    response = auth_client.delete("/api/categories/1")
    assert response.status_code == 403
    app.dependency_overrides.clear()

def test_update_master_category_retorna_403_prohibido(auth_client):
    """Prueba que un inquilino no puede renombrar una Master Category global."""
    app.dependency_overrides[get_current_user] = lambda: {"sub": "tenant_1", "role": "tenant"}
    payload = {"name": "Hack"}
    response = auth_client.put("/api/categories/1", json=payload)
    assert response.status_code == 403
    app.dependency_overrides.clear()
