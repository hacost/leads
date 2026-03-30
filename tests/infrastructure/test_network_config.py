import os
import pytest
from src.core.config import ALLOWED_ORIGINS

def test_env_contains_valid_network_ip():
    """
    Valida que la variable ALLOWED_ORIGINS en el .env contenga una IP de red válida (LAN).
    """
    # Validamos que al menos uno de los orígenes sea una IP de red privada (RFC 1918)
    assert any(
        "192.168." in o or "172." in o or "10." in o for o in ALLOWED_ORIGINS
    ), "ALLOWED_ORIGINS debe contener al menos una IP de red local (LAN) para acceso profesional."

def test_cors_config_loading():
    """
    Verifica que src/core/config.py cargue correctamente la lista de orígenes.
    """
    assert isinstance(ALLOWED_ORIGINS, list)
    assert len(ALLOWED_ORIGINS) >= 2
    assert any("localhost" in o for o in ALLOWED_ORIGINS)
    assert any("." in o and "127.0.0.1" not in o for o in ALLOWED_ORIGINS), \
        "Debe haber al menos un origen que no sea localhost."
