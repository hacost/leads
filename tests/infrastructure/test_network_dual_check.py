import socket
import pytest
import os

def get_local_ip():
    """Detecta la IP local de forma similar a start_dev.sh"""
    try:
        # Comando para macOS
        import subprocess
        return subprocess.check_output(['ipconfig', 'getifaddr', 'en0']).decode().strip()
    except:
        return "127.0.0.1"

@pytest.mark.e2e
def test_dual_frontend_connectivity():
    """
    E2E: Verifica que el puerto 3000 acepte conexiones en 127.0.0.1 y en la IP de red.
    REQUIERE: que Next.js esté corriendo (`npm run dev`).
    Ejecutar con: pytest -m e2e
    """
    local_ip = get_local_ip()
    ports = [3000]
    hosts = ["127.0.0.1", local_ip]
    
    for host in hosts:
        for port in ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((host, port))
                assert result == 0, f"No se pudo conectar a {host}:{port}. ¿Servicio apagado o binding incorrecto?"

@pytest.mark.e2e
def test_dual_api_connectivity():
    """
    E2E: Verifica que el puerto 8000 acepte conexiones en 127.0.0.1 y en la IP de red.
    REQUIERE: que la API FastAPI esté corriendo (`uvicorn ...`).
    Ejecutar con: pytest -m e2e
    """
    local_ip = get_local_ip()
    ports = [8000]
    hosts = ["127.0.0.1", local_ip]
    
    for host in hosts:
        for port in ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((host, port))
                assert result == 0, f"No se pudo conectar a {host}:{port}. ¿Servicio apagado o binding incorrecto?"

