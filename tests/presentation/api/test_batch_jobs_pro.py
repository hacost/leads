import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from src.presentation.api.main import app
from src.presentation.api.auth import get_current_user

# ===========================================================================
# Batch Builder PRO - Multi-Targeting Tests
# Archivo: tests/presentation/api/test_batch_jobs_pro.py
# Estrategia: TestClient FastAPI + Mocks robustos para StorageService
# ESTADO OBJETIVO: ROJO - Endpoint POST /api/jobs/batch no existe aún.
# ===========================================================================

client = TestClient(app, raise_server_exceptions=False)

TENANT_USER = {"sub": "tenant_1", "role": "tenant"}

def override_tenant():
    return TENANT_USER


# ---------------------------------------------------------------------------
# Test 1 — POST /api/jobs/batch: Crear N jobs por state_id
# ---------------------------------------------------------------------------
def test_create_batch_jobs_by_state_id():
    """
    Simula seleccionar 'Todo el Estado' en el Front.
    El endpoint debe recibir state_id, buscar las ciudades, e insertar los trabajos
    usando batch payload.
    Error Esperado (ROJO): 404 porque el endpoint no existe.
    """
    app.dependency_overrides[get_current_user] = override_tenant
    
    payload = {
        "category_id": 1,
        "state_id": 1,
        "max_leads": 50,
        "city_id": None,
        "all_cities": False
    }

    res = client.post("/api/jobs/batch", json=payload)
    app.dependency_overrides.clear()
    
    assert res.status_code == 201
    assert "Enqueued" in res.json()["message"]


# ---------------------------------------------------------------------------
# Test 2 — POST /api/jobs/batch: Crear N jobs Nivel Nacional (all_cities)
# ---------------------------------------------------------------------------
def test_create_batch_jobs_global():
    """
    Simula seleccionar 'Nivel Nacional' en el Front.
    El endpoint debe insertar trabajos para TODAS las ciudades en db.
    Error Esperado (ROJO): 404 porque el endpoint no existe.
    """
    app.dependency_overrides[get_current_user] = override_tenant
    
    payload = {
        "category_id": 1,
        "all_cities": True,
        "max_leads": 100,
        "city_id": None,
        "state_id": None
    }

    res = client.post("/api/jobs/batch", json=payload)
    app.dependency_overrides.clear()
    
    assert res.status_code == 201
    assert "Enqueued" in res.json()["message"]


# ---------------------------------------------------------------------------
# Test 3 — POST /api/jobs/batch: Bad Request si no se envía target
# ---------------------------------------------------------------------------
def test_create_batch_jobs_missing_target():
    """
    Valida que se envíe al menos city_id, state_id o all_cities.
    """
    app.dependency_overrides[get_current_user] = override_tenant
    
    payload = {
        "category_id": 1,
        "max_leads": 50
    }

    res = client.post("/api/jobs/batch", json=payload)
    app.dependency_overrides.clear()
    
    assert res.status_code == 400
    assert res.json()["detail"] == "Must specify city_id, state_id, or all_cities=true"
