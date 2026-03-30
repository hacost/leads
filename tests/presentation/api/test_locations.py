import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from src.presentation.api.main import app
from src.presentation.api.auth import get_current_user

# ===========================================================================
# SPRINT 3 — API: Endpoints Jerárquicos + RBAC
# Archivo: tests/presentation/api/test_locations.py
# Estrategia: TestClient FastAPI + dependency_overrides para auth.
# ESTADO OBJETIVO: ROJO — El módulo src/presentation/api/locations.py no existe aún.
# ===========================================================================

client = TestClient(app, raise_server_exceptions=False)

# ---------------------------------------------------------------------------
# Identidades de prueba
# ---------------------------------------------------------------------------
ADMIN_USER  = {"sub": "admin_1",  "role": "admin"}
TENANT_USER = {"sub": "tenant_1", "role": "tenant"}


def override_admin():
    return ADMIN_USER

def override_tenant():
    return TENANT_USER


# ---------------------------------------------------------------------------
# Test 3.1 — GET /api/countries devuelve 200 para usuario autenticado
# ---------------------------------------------------------------------------
def test_get_countries_200():
    app.dependency_overrides[get_current_user] = override_tenant
    mock_data = [{"id": 1, "name": "Mexico"}]
    with patch("src.presentation.api.locations.StorageService.get_countries", return_value=mock_data):
        res = client.get("/api/countries")
    app.dependency_overrides.clear()
    assert res.status_code == 200
    assert res.json()[0]["name"] == "Mexico"


# ---------------------------------------------------------------------------
# Test 3.2 — GET /api/countries devuelve 401 sin token
# ---------------------------------------------------------------------------
def test_get_countries_401_without_token():
    app.dependency_overrides.clear()
    res = client.get("/api/countries")
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# Test 3.3 — POST /api/countries devuelve 201 para admin
# ---------------------------------------------------------------------------
def test_create_country_201_for_admin():
    app.dependency_overrides[get_current_user] = override_admin
    with patch("src.presentation.api.locations.StorageService.create_country", return_value=1):
        res = client.post("/api/countries", json={"name": "USA"})
    app.dependency_overrides.clear()
    assert res.status_code == 201


# ---------------------------------------------------------------------------
# Test 3.4 — POST /api/countries devuelve 403 para rol no-admin
# ---------------------------------------------------------------------------
def test_create_country_403_for_non_admin():
    app.dependency_overrides[get_current_user] = override_tenant
    res = client.post("/api/countries", json={"name": "USA"})
    app.dependency_overrides.clear()
    assert res.status_code == 403


# ---------------------------------------------------------------------------
# Test 3.5 — GET /api/states?country_id=1 retorna estados filtrados
# ---------------------------------------------------------------------------
def test_get_states_filtered_by_country_id():
    app.dependency_overrides[get_current_user] = override_tenant
    mock_data = [{"id": 1, "name": "NL", "country_id": 1}]
    with patch("src.presentation.api.locations.StorageService.get_states_by_country", return_value=mock_data):
        res = client.get("/api/states?country_id=1")
    app.dependency_overrides.clear()
    assert res.status_code == 200
    assert res.json()[0]["country_id"] == 1


# ---------------------------------------------------------------------------
# Test 3.6 — POST /api/states devuelve 201 para admin
# ---------------------------------------------------------------------------
def test_create_state_201_for_admin():
    app.dependency_overrides[get_current_user] = override_admin
    with patch("src.presentation.api.locations.StorageService.create_state", return_value=1):
        res = client.post("/api/states", json={"name": "NL", "country_id": 1})
    app.dependency_overrides.clear()
    assert res.status_code == 201


# ---------------------------------------------------------------------------
# Test 3.7.5 — GET /api/cities?state_id=X retorna ciudades filtradas (Batch PRO)
# ---------------------------------------------------------------------------
def test_get_cities_filtered_by_state_id():
    """
    Error Esperado (ROJO): Actualmente el mock o la DB asume que devuelve todas las master_cities.
    La prueba verificará que si mandamos state_id=1, el mock reciba exactamente state_id=1.
    """
    app.dependency_overrides[get_current_user] = override_tenant
    mock_data = [{
        "id": 1, "name": "Monterrey", "state_id": 1,
        "state_name": "NL", "country_name": "Mexico",
        "status": 1, "created_at": None
    }]
    # Interceptamos get_master_cities y verificamos que fue llamado con state_id=1
    with patch("src.presentation.api.locations.StorageService.get_master_cities", return_value=mock_data) as mock_get_cities:
        res = client.get("/api/cities?state_id=1")
        mock_get_cities.assert_called_once_with(limit=100, offset=0, state_id=1)
    
    app.dependency_overrides.clear()
    assert res.status_code == 200
    assert res.json()[0]["state_id"] == 1

# ---------------------------------------------------------------------------
# Test 3.7 — GET /api/cities incluye state_name y country_name del triple JOIN
# ---------------------------------------------------------------------------
def test_get_cities_includes_hierarchy():
    app.dependency_overrides[get_current_user] = override_tenant
    mock_data = [{
        "id": 1, "name": "Monterrey", "state_id": 1,
        "state_name": "NL", "country_name": "Mexico",
        "status": 1, "created_at": None
    }]
    with patch("src.presentation.api.locations.StorageService.get_master_cities", return_value=mock_data) as mock_get_cities:
        res = client.get("/api/cities")
        # Por defecto se llama sin parámetros explícitos desde la url, pero fastapi pone limit, offset y state_id
        mock_get_cities.assert_called_once_with(limit=100, offset=0, state_id=None)
    app.dependency_overrides.clear()
    assert res.status_code == 200
    assert res.json()[0]["state_name"] == "NL"
    assert res.json()[0]["country_name"] == "Mexico"


# ---------------------------------------------------------------------------
# Test 3.8 — POST /api/cities sin state_id devuelve 422 (validación Pydantic)
# ---------------------------------------------------------------------------
def test_create_city_422_without_state_id():
    """
    Sin state_id el endpoint debe devolver 422 (validación Pydantic).
    En ROJO: devuelve 404 porque /api/cities POST aún no existe.
    En VERDE: devolverá 422 cuando el router esté registrado.
    """
    app.dependency_overrides[get_current_user] = override_admin
    with patch("src.presentation.api.locations.StorageService.create_master_city", return_value=1):
        res = client.post("/api/cities", json={"name": "Monterrey"})  # Falta state_id
    app.dependency_overrides.clear()
    app.dependency_overrides.clear()
    assert res.status_code == 422

# ---------------------------------------------------------------------------
# Test 3.9 — PUT /api/countries/{id} y PUT /api/states/{id}
# ---------------------------------------------------------------------------
def test_update_country_and_state_endpoints_exist_and_require_admin():
    # Intento sin admin -> 403
    app.dependency_overrides[get_current_user] = override_tenant
    assert client.put("/api/countries/1", json={"name": "Can"}).status_code == 403
    assert client.put("/api/states/1", json={"name": "Ont", "country_id": 1}).status_code == 403
    
    # Intento con admin -> 200 OK (requiere mocks verdes)
    app.dependency_overrides[get_current_user] = override_admin
    with patch("src.presentation.api.locations.StorageService.update_country", return_value=True):
        res = client.put("/api/countries/1", json={"name": "Canada"})
        assert res.status_code == 200
        assert res.json()["name"] == "Canada"
        
    with patch("src.presentation.api.locations.StorageService.update_state", return_value=True):
        res = client.put("/api/states/1", json={"name": "Ontario", "country_id": 1})
        assert res.status_code == 200
        assert res.json()["name"] == "Ontario"
    app.dependency_overrides.clear()

# ---------------------------------------------------------------------------
# Test 3.10 — DELETE /api/states/{id} (Cascade Soft Delete)
# ---------------------------------------------------------------------------
def test_delete_state_requires_admin_and_returns_204():
    app.dependency_overrides[get_current_user] = override_tenant
    assert client.delete("/api/states/5").status_code == 403
    
    app.dependency_overrides[get_current_user] = override_admin
    with patch("src.presentation.api.locations.StorageService.delete_state_with_cascade", return_value=True) as mock_delete:
        res = client.delete("/api/states/5")
        mock_delete.assert_called_once_with(5)
        assert res.status_code == 204
    app.dependency_overrides.clear()
