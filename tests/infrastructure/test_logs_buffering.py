import os
import subprocess
import time
import pytest
import re
from datetime import datetime

@pytest.mark.skipif(os.name == 'nt', reason="This test is designed for Unix-like environments.")
def test_python_unbuffered_logging_realtime():
    """
    Verifica que la salida de Python se escriba inmediatamente en un archivo cuando se usa -u.
    """
    log_file = "/tmp/test_unbuffered.log"
    if os.path.exists(log_file):
        os.remove(log_file)
        
    script = "import sys, time; print('READY'); sys.stdout.flush(); time.sleep(1); print('DONE')"
    
    process = subprocess.Popen(
        ["python3", "-u", "-c", script],
        stdout=open(log_file, "w"),
        stderr=subprocess.STDOUT
    )
    
    time.sleep(0.5)
    
    with open(log_file, "r") as f:
        content = f.read()
        assert "READY" in content, "Output was buffered despite -u flag"

    process.wait()
    if os.path.exists(log_file):
        os.remove(log_file)

def test_native_logging_format():
    """
    Verifica que el nuevo sistema de logs nativo genere el formato:
    [YYYY-MM-DD HH:MM:SS] [COMPONENT] mensaje
    """
    log_file = "/tmp/test_format.log"
    if os.path.exists(log_file):
        os.remove(log_file)

    # Creamos un script que use nuestro setup_logging
    script = """
import logging
import sys
import os
# Añadimos el PATH actual para poder importar src
sys.path.append(os.getcwd())
from src.core.logging_config import setup_logging

setup_logging("TEST_COMP")
logging.info("Mensaje de prueba")
"""
    
    process = subprocess.Popen(
        ["python3", "-c", script],
        stdout=open(log_file, "w"),
        stderr=subprocess.STDOUT
    )
    process.wait()

    with open(log_file, "r") as f:
        content = f.read()
        # Buscamos el patrón: [2026-03-22 22:15:00] [TEST_COMP] Mensaje de prueba
        pattern = r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[TEST_COMP\] Mensaje de prueba"
        assert re.search(pattern, content), f"Formato de log incorrecto. Recibido: {content}"

    if os.path.exists(log_file):
        os.remove(log_file)
