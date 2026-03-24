import os
import sys

# Asegurar que el directorio raíz está en el path
sys.path.append(os.getcwd())

from fastapi.testclient import TestClient
from src.presentation.api.main import app

def run_red_test():
    """
    Test determinista para verificar el rechazo de CORS de una IP remota.
    """
    client = TestClient(app)
    remote_origin = "http://192.168.100.22:3000"
    
    print(f"Probando preflight (OPTIONS) desde origen remoto: {remote_origin}")
    
    response = client.options(
        "/api/auth/request-otp",
        headers={
            "Origin": remote_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        }
    )
    
    status = response.status_code
    allow_origin = response.headers.get("access-control-allow-origin")
    
    print(f"Resultado -> Status: {status}, Access-Control-Allow-Origin: {allow_origin}")
    
    # Actualmente en main.py solo se permite localhost/127.0.0.1
    # Por lo tanto, el header access-control-allow-origin debería ser None o distinto
    if allow_origin != remote_origin:
        print("ESTADO ROJO CONFIRMADO: El origen remoto fue RECHAZADO.")
        return True
    else:
        print("ERROR: El origen remoto fue PERMITIDO (esto no debería pasar en el estado actual).")
        return False

if __name__ == "__main__":
    if run_red_test():
        sys.exit(0)
    else:
        sys.exit(1)
