import pytest
from fastapi.testclient import TestClient
from src.presentation.api.main import app

client = TestClient(app)

def test_cors_allows_localhost_origin():
    """
    Verifica que las peticiones desde localhost:3000 sean permitidas.
    """
    origin = "http://localhost:3000"
    response = client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin

def test_cors_allows_remote_network_origin():
    """
    Verifica que la IP de la red local configurada en el .env sea aceptada.
    """
    from src.core.config import ALLOWED_ORIGINS
    # Buscamos un origen que parezca una IP de LAN (no localhost, no 127.0.0.1)
    remote_ip_origin = next((o for o in ALLOWED_ORIGINS if "localhost" not in o and "127.0.0.1" not in o), None)
    
    if not remote_ip_origin:
        pytest.skip("No se encontró una IP remota en ALLOWED_ORIGINS para probar.")
        
    response = client.options(
        "/health",
        headers={
            "Origin": remote_ip_origin,
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == remote_ip_origin

def test_cors_full_matrix():
    """
    Verifica que localhost, 127.0.0.1 y la IP de red configurada funcionen.
    """
    from src.core.config import ALLOWED_ORIGINS
    
    for origin in ALLOWED_ORIGINS:
        response = client.options(
            "/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.status_code == 200, f"Error en CORS para el origen permitido: {origin}"
        assert response.headers.get("access-control-allow-origin") == origin

def test_cors_denies_unauthorized_origin():
    """
    Verifica que orígenes no autorizados no reciban headers de CORS.
    """
    origin = "http://evil-hack.com"
    response = client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.headers.get("access-control-allow-origin") is None

def test_cors_preflight_options_work():
    """
    Valida que las peticiones OPTIONS funcionen correctamente.
    """
    origin = "http://localhost:3000"
    response = client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert "GET" in response.headers.get("access-control-allow-methods", "")
