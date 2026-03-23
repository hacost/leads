import logging
import sys
from datetime import datetime

class ComponentFormatter(logging.Formatter):
    """
    Formatter para incluir [Timestamp] [Componente] mensaje.
    Garantiza el formato solicitado por el usuario: [2026-03-22 22:33:00] [COMP]
    """
    def __init__(self, component_name: str):
        super().__init__()
        self.component_name = component_name

    def format(self, record):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp}] [{self.component_name}] {record.getMessage()}"

def setup_logging(component_name: str, level=logging.INFO):
    """
    Configuración de logging senior con formato de marca de tiempo y componente.
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Limpiar handlers previos para evitar duplicados
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    # Usar sys.stdout directamente (sin interceptaciones complejas por ahora para estabilidad)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ComponentFormatter(component_name))
    logger.addHandler(handler)
    
    # Silenciar ruidos externos
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)
    
    return logger
