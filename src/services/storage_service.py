import os
import glob
from typing import List

class StorageService:
    """
    Módulo encargado de manejar todo el almacenamiento (I/O). 
    Actualmente guarda y lee de disco local, pero si en el futuro se quiere 
    subir a la nube (AWS S3, Google Drive, etc.), solo se cambia este archivo
    y ninguna otra parte del Agente se rompe.
    """
    
    @staticmethod
    def get_session_directory(session_id: str) -> str:
        """Devuelve la ruta estandarizada para guardar o buscar archivos de un usuario."""
        return f"leads/session_{session_id}"
        
    @staticmethod
    def fetch_excel_files_for_session(session_id: str) -> List[str]:
        """
        Busca todos los archivos Excel generados en la carpeta de la sesión.
        """
        specific_dir = StorageService.get_session_directory(session_id)
        if os.path.exists(specific_dir):
            return glob.glob(os.path.join(specific_dir, '*.xlsx'))
        return []

# Puedes usar estas funciones simples importándolas directamente
def buscar_excels_de_usuario(session_id: str) -> List[str]:
    return StorageService.fetch_excel_files_for_session(session_id)

def obtener_ruta_directorio(session_id: str) -> str:
    return StorageService.get_session_directory(session_id)
