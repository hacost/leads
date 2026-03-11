import os
import glob
import glob
import sqlite3
import json
from typing import List, Dict, Optional

DB_PATH = "data/bastion_bot.db"

def _init_db():
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                cron_expression TEXT NOT NULL,
                prompt_task TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1
            )
        ''')
        conn.commit()

_init_db()

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

    @staticmethod
    def guardar_excel(df, session_id: str, filename: str) -> str:
        """
        Guarda un DataFrame como archivo Excel aislando a Pandas y os.path 
        del resto del Agente y los Scrapers.
        Si session_id es nulo, usa timestamp (para ejecuciones manuales).
        """
        if session_id:
            output_dir = StorageService.get_session_directory(session_id)
        else:
            import time
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
            output_dir = os.path.join("leads", timestamp)
            
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, filename)
        df.to_excel(file_path, index=False)
        return file_path

    @staticmethod
    def obtener_stream_archivo(ruta: str):
        """
        Abre un archivo (en disco o nube en un futuro) para que la UI 
        lo envíe sin saber de dónde viene realmente.
        """
        return open(ruta, 'rb')
        
    @staticmethod
    def obtener_nombre_archivo(ruta: str) -> str:
        """Abstrae la extracción del nombre del archivo sin que la UI importe OS."""
        return os.path.basename(ruta)

    @staticmethod
    def eliminar_sesion(session_id: str):
        """
        Elimina la carpeta de la sesión actual y todos sus archivos Excel.
        Esto previene que búsquedas fallidas envíen adjuntos de búsquedas anteriores.
        """
        specific_dir = StorageService.get_session_directory(session_id)
        if os.path.exists(specific_dir):
            import shutil
            shutil.rmtree(specific_dir, ignore_errors=True)
            print(f"   🧹 [Limpieza] Carpeta de sesión eliminada: {specific_dir}")

            print(f"   🧹 [Limpieza] Carpeta de sesión eliminada: {specific_dir}")

    # ==========================================
    # LÓGICA DE BASE DE DATOS PARA ALERTAS (PHASE 2)
    # ==========================================
    
    @staticmethod
    def guardar_alerta(chat_id: str, cron_expression: str, prompt_task: str) -> int:
        """Guarda una nueva alerta en SQLite y devuelve su ID."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO scheduled_alerts (chat_id, cron_expression, prompt_task, is_active) VALUES (?, ?, ?, 1)",
                (str(chat_id), cron_expression, prompt_task)
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def obtener_alertas(chat_id: Optional[str] = None) -> List[Dict]:
        """Obtiene las alertas activas, opcionalmente filtradas por chat_id."""
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if chat_id:
                cursor.execute("SELECT * FROM scheduled_alerts WHERE is_active=1 AND chat_id=?", (str(chat_id),))
            else:
                cursor.execute("SELECT * FROM scheduled_alerts WHERE is_active=1")
            
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def eliminar_alerta(alerta_id: int, chat_id: Optional[str] = None) -> bool:
        """Marca una alerta como inactiva (eliminada lógicamente). Opcionalmente verifica propiedad."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            if chat_id:
                cursor.execute("UPDATE scheduled_alerts SET is_active=0 WHERE id=? AND chat_id=?", (alerta_id, str(chat_id)))
            else:
                cursor.execute("UPDATE scheduled_alerts SET is_active=0 WHERE id=?", (alerta_id,))
            conn.commit()
            return cursor.rowcount > 0

# Puedes usar estas funciones simples importándolas directamente
def buscar_excels_de_usuario(session_id: str) -> List[str]:
    return StorageService.fetch_excel_files_for_session(session_id)

def obtener_ruta_directorio(session_id: str) -> str:
    return StorageService.get_session_directory(session_id)
