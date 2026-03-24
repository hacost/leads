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

def test_dual_frontend_connectivity():
    """
    Verifica que el puerto 3000 acepte conexiones en 127.0.0.1 y en la IP de red.
    En fase ROJA, 127.0.0.1 fallará si Next.js está en -H $IP.
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

def test_dual_api_connectivity():
    """
    Verifica que el puerto 8000 acepte conexiones en 127.0.0.1 y en la IP de red.
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
