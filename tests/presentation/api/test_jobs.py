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
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    app.dependency_overrides.clear()

def test_get_jobs_sin_token_retorna_401():
    response = client.get("/api/jobs")
    assert response.status_code in [401, 403]

@patch("src.presentation.api.jobs.StorageService")
def test_get_jobs_con_token_valido_retorna_200(mock_storage, auth_client):
    mock_storage.get_jobs.return_value = []
    response = auth_client.get("/api/jobs", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@patch("src.presentation.api.jobs.StorageService")
def test_create_job_con_datos_validos_retorna_201_o_200(mock_storage, auth_client):
    mock_storage.create_hybrid_job.return_value = 42
    response = auth_client.post("/api/jobs", json={"category_id": 1, "city_id": 1}, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code in [200, 201]
    
    data = response.json()
    assert "id" in data
    assert data["id"] == 42
    
@patch("src.presentation.api.jobs.StorageService")
def test_create_job_flexible_sin_ids_retorna_200_o_201(mock_storage, auth_client):
    """Verifica que el endpoint acepta jobs sin IDs si se provee texto (Hybrid)."""
    mock_storage.create_hybrid_job.return_value = 100
    response = auth_client.post("/api/jobs", json={"categoria_text": "Dentistas", "zona_text": "Madrid"}, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code in [200, 201]
    assert response.json()["id"] == 100

@patch("src.presentation.api.jobs.StorageService")
def test_get_job_by_id_con_id_valido_retorna_200(mock_storage, auth_client):
    mock_storage.get_job_by_id.return_value = {
        "id": 1, "category_id": 1, "city_id": 1, "owner_id": "test_chat_123", 
        "status": "pending", "category_name": "Dentists", "city_name": "Monterrey", "created_at": "2026-03-22"
    }
    response = auth_client.get("/api/jobs/1", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["city_name"] == "Monterrey"

@patch("src.presentation.api.jobs.StorageService")
def test_get_job_by_id_con_id_invalido_retorna_404(mock_storage, auth_client):
    mock_storage.get_job_by_id.return_value = None
    response = auth_client.get("/api/jobs/999", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 404

@patch("src.presentation.api.jobs.StorageService")
def test_retry_job_updates_status_returns_200(mock_storage, auth_client):
    mock_storage.retry_job.return_value = True
    response = auth_client.patch("/api/jobs/1/retry", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 200
    assert response.json()["message"] == "Job rescheduled for processing"

@patch("src.presentation.api.jobs.StorageService")
def test_get_jobs_with_pagination_params(mock_storage, auth_client):
    mock_storage.get_jobs.return_value = []
    response = auth_client.get("/api/jobs?limit=5&offset=10", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 200
    # Verificamos que se pasaron los parámetros al storage (esto fallará si el endpoint no captura limit/offset)
    mock_storage.get_jobs.assert_called_with(owner_id="test_chat_123", limit=5, offset=10)

@patch("src.presentation.api.admin.StorageService")
def test_get_worker_health_endpoint_exists(mock_storage, auth_client):
    """Prueba que el endpoint para el Badge del dashboard existe."""
    mock_storage.get_worker_health.return_value = {"status": "online", "last_heartbeat": "2026-03-22 20:00:00"}
    response = auth_client.get("/api/admin/worker/health", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 200
    assert response.json()["status"] == "online"

@patch("src.presentation.api.jobs.StorageService")
def test_get_jobs_hybrid_mapping_uses_text_if_id_is_null(mock_storage, auth_client):
    """
    Verifica que si los IDs son nulos (Job del Bot), BatchJobView mapea 
    los campos de texto a los nombres de categoría/ciudad para el Dashboard.
    """
    mock_storage.get_jobs.return_value = [
        {
            "id": 1, 
            "category_id": None, 
            "city_id": None, 
            "categoria_text": "Restaurantes", 
            "zona_text": "Barcelona",
            "owner_id": "test_chat_123",
            "status": "pending",
            "category_name": None,  # El Join de SQL devuelve NULL
            "city_name": None
        }
    ]
    response = auth_client.get("/api/jobs", headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 200
    data = response.json()[0]
    
    # El modelo debe haber resuelto los nombres usando los campos de texto
    assert data["category_name"] == "Restaurantes"
    assert data["city_name"] == "Barcelona"

@patch("src.presentation.api.jobs.StorageService")
def test_create_job_requires_minimal_data(mock_storage, auth_client):
    """
    PRUEBA ROJA: Verifica que la API rechaza un objeto vacío.
    Debe fallar con 422 Unprocessable Entity en lugar de crear un job fantasma.
    """
    response = auth_client.post("/api/jobs", json={}, headers={"Authorization": "Bearer fake_token"})
    assert response.status_code == 422
