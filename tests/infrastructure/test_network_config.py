import os
import pytest
from src.core.config import ALLOWED_ORIGINS

def test_env_contains_valid_network_ip():
    """
    Valida que la variable ALLOWED_ORIGINS en el .env contenga una IP de red válida.
    """
    # Intentamos leer el archivo .env directamente o el entorno
    origins = os.getenv("ALLOWED_ORIGINS", "")
    assert "192.168.100.22" in origins or "172." in origins or "10." in origins, \
        "ALLOWED_ORIGINS debe contener la IP de la red local para acceso profesional."

def test_cors_config_loading():
    """
    Verifica que src/core/config.py cargue correctamente la lista de orígenes.
    """
    assert isinstance(ALLOWED_ORIGINS, list)
    assert len(ALLOWED_ORIGINS) >= 2
    assert any("localhost" in o for o in ALLOWED_ORIGINS)
    assert any("." in o and "127.0.0.1" not in o for o in ALLOWED_ORIGINS), \
        "Debe haber al menos un origen que no sea localhost."
