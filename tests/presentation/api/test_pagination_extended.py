import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from src.presentation.api.main import app
from src.presentation.api.auth import get_current_user

client = TestClient(app)

def override_get_current_user():
    return {"sub": "test_user", "role": "admin"}

@pytest.fixture
def auth_client():
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    app.dependency_overrides.clear()

def test_get_categories_with_dynamic_pagination(auth_client):
    """Verifica que el endpoint de categorías acepte limit dinámico (10, 20, 50, 100)."""
    with patch("src.infrastructure.database.storage_service.StorageService.get_categories") as mock_get:
        mock_get.return_value = []
        
        for limit in [10, 20, 30, 50, 100]:
            response = auth_client.get(f"/api/categories?limit={limit}&offset=0")
            assert response.status_code == 200
            mock_get.assert_called_with(owner_id="test_user", limit=limit, offset=0)

def test_get_cities_with_dynamic_pagination(auth_client):
    """Verifica que el endpoint de ciudades acepte limit dinámico (10, 20, 50, 100)."""
    with patch("src.infrastructure.database.storage_service.StorageService.get_master_cities") as mock_get:
        mock_get.return_value = []
        
        for limit in [10, 20, 30, 50, 100]:
            response = auth_client.get(f"/api/cities?limit={limit}&offset=0")
            assert response.status_code == 200
            mock_get.assert_called_with(limit=limit, offset=0)

def test_get_jobs_with_various_limits(auth_client):
    """Verifica que el endpoint de jobs acepte límites de 10, 20, 30, 50 y 100."""
    with patch("src.infrastructure.database.storage_service.StorageService.get_jobs") as mock_get:
        mock_get.return_value = []
        
        for limit in [10, 20, 30, 50, 100]:
            response = auth_client.get(f"/api/jobs?limit={limit}&offset=0")
            assert response.status_code == 200
            mock_get.assert_called_with(owner_id="test_user", limit=limit, offset=0)
