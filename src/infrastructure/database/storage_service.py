import os
import glob
import glob
import sqlite3
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

DB_PATH = "data/bastion_bot.db"
LEADS_DB_PATH = "data/leads.db"

def _create_tables(conn):
    """Crea el esquema normalizado Country→State→City sobre la conexión dada."""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS master_countries (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS master_states (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            country_id INTEGER NOT NULL,
            FOREIGN KEY (country_id) REFERENCES master_countries(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_alerts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id         TEXT    NOT NULL,
            cron_expression TEXT    NOT NULL,
            prompt_task     TEXT    NOT NULL,
            is_active       BOOLEAN NOT NULL DEFAULT 1
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS master_cities (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            state_id   INTEGER,
            status     INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (state_id) REFERENCES master_states(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_sessions (
            chat_id     TEXT PRIMARY KEY,
            session_id  TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS worker_config (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS master_categories (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            name   TEXT    NOT NULL,
            status INTEGER NOT NULL DEFAULT 1
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS batch_jobs (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id    INTEGER,
            city_id        INTEGER,
            zona_text      TEXT,
            categoria_text TEXT,
            owner_id       TEXT NOT NULL,
            status         TEXT NOT NULL DEFAULT 'pending',
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (city_id)     REFERENCES master_cities(id),
            FOREIGN KEY (category_id) REFERENCES master_categories(id)
        )
    ''')
    for col in ("zona_text", "categoria_text"):
        try:
            cursor.execute(f"ALTER TABLE batch_jobs ADD COLUMN {col} TEXT")
        except Exception:
            pass
    for table in ["master_countries", "master_states"]:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN status INTEGER NOT NULL DEFAULT 1")
        except Exception:
            pass
    cursor.execute("DROP TABLE IF EXISTS tenant_categories")
    cursor.execute("DROP TABLE IF EXISTS countries")
    cursor.execute("DROP TABLE IF EXISTS states")
    conn.commit()


def _init_db(conn_override=None):
    """
    Inicializa el esquema de la BD.
    - conn_override: conexión SQLite externa (tests con :memory:). Crea tablas y retorna.
    - Sin override: usa DB_PATH, crea tablas y NO siembra datos (per clean DB spec).
    """
    if conn_override is not None:
        _create_tables(conn_override)
        return
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        _create_tables(conn)


_init_db()

class StorageService:
    """
    Módulo encargado de manejar todo el almacenamiento (I/O). 
    Actualmente guarda y lee de disco local, pero si en el futuro se quiere 
    subir a la nube (AWS S3, Google Drive, etc.), solo se cambia este archivo
    y ninguna otra parte del Agente se rompe.
    """
    
    @staticmethod
    def get_db_path() -> str:
        return DB_PATH

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
            logger.info(f"   🧹 [Limpieza] Carpeta de sesión eliminada: {specific_dir}")

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

    # ==========================================
    # LÓGICA DE BASE DE DATOS PARA REQUISITOS BATCH (PHASE 2.5)
    # ==========================================

    @staticmethod
    def get_master_cities(limit: int = 100, offset: int = 0, state_id: Optional[int] = None, conn_override=None):
        base_query = '''
            SELECT mc.id, mc.name, mc.state_id, mc.status, mc.created_at,
                   s.name  AS state_name,
                   co.name AS country_name
            FROM master_cities mc
            LEFT JOIN master_states    s  ON mc.state_id  = s.id
            LEFT JOIN master_countries co ON s.country_id = co.id
            WHERE mc.status = 1
        '''
        params = []
        if state_id is not None:
            base_query += " AND mc.state_id = ?"
            params.append(state_id)
            
        base_query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        if conn_override is not None:
            conn_override.row_factory = sqlite3.Row
            cursor = conn_override.cursor()
            cursor.execute(base_query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(base_query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def create_master_city(name: str, state_id: int, conn_override=None) -> int:
        """Crea una nueva ciudad vinculada a un estado del catálogo."""
        if conn_override is not None:
            cursor = conn_override.cursor()
            cursor.execute("INSERT INTO master_cities (name, state_id, status) VALUES (?, ?, 1)", (name, state_id))
            conn_override.commit()
            return cursor.lastrowid
        with sqlite3.connect(StorageService.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO master_cities (name, state_id, status) VALUES (?, ?, 1)", (name, state_id))
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def update_master_city(city_id: int, name: str, state_id: int) -> bool:
        with sqlite3.connect(StorageService.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE master_cities SET name=?, state_id=? WHERE id=?", (name, state_id, city_id))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def delete_master_city(city_id: int) -> bool:
        with sqlite3.connect(StorageService.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM master_cities WHERE id=?", (city_id,))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def get_or_create_city(name: str) -> Optional[int]:
        """
        Busca una ciudad por nombre (case-insensitive).
        NOTA: El catálogo es cerrado — ya NO crea ciudades. Devuelve None si no existe.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM master_cities WHERE name COLLATE NOCASE = ?", (name,))
            row = cursor.fetchone()
            return row[0] if row else None

    @staticmethod
    def get_city_by_name(name: str) -> Optional[dict]:
        """Busca una ciudad por nombre exacto (case-insensitive) para validación."""
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM master_cities WHERE name COLLATE NOCASE = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_categories():
        """Retorna TODAS las categorías maestras globales. (Eliminamos parám owner_id por ser global)."""
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM master_categories WHERE status=1 ORDER BY name ASC")
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def create_category(name: str) -> int:
        """Crea una categoría maestra global."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO master_categories (name) VALUES (?)",
                (name,)
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def update_category_status(category_id: int, new_status: int) -> bool:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE master_categories SET status=? WHERE id=?", (new_status, category_id))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def delete_category(category_id: int) -> bool:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM master_categories WHERE id=?", (category_id,))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def get_category_by_name(name: str) -> Optional[dict]:
        """Busca una categoría global por nombre exacto (case-insensitive) para validación del Bot."""
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM master_categories WHERE name COLLATE NOCASE = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ==========================================
    # CATÁLOGO NORMALIZADO: COUNTRIES & STATES
    # ==========================================

    @staticmethod
    def create_country(name: str, conn_override=None) -> int:
        """Crea un país en el catálogo global. Devuelve su ID."""
        if conn_override is not None:
            cursor = conn_override.cursor()
            cursor.execute("INSERT INTO master_countries (name) VALUES (?)", (name,))
            conn_override.commit()
            return cursor.lastrowid
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO master_countries (name) VALUES (?)", (name,))
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def create_state(name: str, country_id: int, conn_override=None) -> int:
        """Crea un estado vinculado a un país. Devuelve su ID."""
        try:
            if conn_override is not None:
                cursor = conn_override.cursor()
                cursor.execute(
                    "INSERT INTO master_states (name, country_id) VALUES (?, ?)", 
                    (name, country_id)
                )
                conn_override.commit()
                return cursor.lastrowid
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO master_states (name, country_id) VALUES (?, ?)", 
                    (name, country_id)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"No existe el country_id {country_id} para ligar este estado.")

    @staticmethod
    def update_country(country_id: int, name: str) -> bool:
        """Actualiza el nombre de un país. Retorna False si no existe."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE master_countries SET name = ? WHERE id = ? AND status = 1", (name, country_id))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def update_state(state_id: int, name: str) -> bool:
        """Actualiza el nombre de un estado. Retorna False si no existe."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE master_states SET name = ? WHERE id = ? AND status = 1", (name, state_id))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def delete_state_with_cascade(state_id: int) -> bool:
        """Hace Soft Delete de un estado y desactiva todas sus ciudades dependientes."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE master_states SET status = 0 WHERE id = ?", (state_id,))
            if cursor.rowcount == 0:
                return False
            cursor.execute("UPDATE master_cities SET status = 0 WHERE state_id = ?", (state_id,))
            conn.commit()
            return True

    @staticmethod
    def get_countries(conn_override=None) -> List[Dict]:
        """Retorna todos los países activos del catálogo."""
        if conn_override is not None:
            conn_override.row_factory = sqlite3.Row
            cursor = conn_override.cursor()
            cursor.execute("SELECT * FROM master_countries WHERE status=1 ORDER BY name ASC")
            return [dict(row) for row in cursor.fetchall()]
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM master_countries WHERE status=1 ORDER BY name ASC")
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_states_by_country(country_id: int, conn_override=None) -> List[Dict]:
        """Retorna todos los estados activos de un país."""
        if conn_override is not None:
            conn_override.row_factory = sqlite3.Row
            cursor = conn_override.cursor()
            cursor.execute("SELECT * FROM master_states WHERE country_id=? AND status=1 ORDER BY name ASC", (country_id,))
            return [dict(row) for row in cursor.fetchall()]
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM master_states WHERE country_id=? AND status=1 ORDER BY name ASC", (country_id,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_jobs(owner_id: str, limit: int = 50, offset: int = 0):
        """Returns batch jobs scoped to the tenant with pagination support."""
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT j.*, c.name as category_name, m.name as city_name 
                FROM batch_jobs j
                LEFT JOIN master_categories c ON j.category_id = c.id
                LEFT JOIN master_cities m ON j.city_id = m.id
                WHERE j.owner_id=?
                ORDER BY j.created_at DESC
                LIMIT ? OFFSET ?
            ''', (owner_id, limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_job_by_id(job_id: int, owner_id: str) -> Optional[dict]:
        with sqlite3.connect(StorageService.get_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT j.*, 
                       COALESCE(c.name, 'Unknown') as category_name, 
                       COALESCE(m.name, 'Unknown') as city_name 
                FROM batch_jobs j
                LEFT JOIN master_categories c ON j.category_id = c.id
                LEFT JOIN master_cities m ON j.city_id = m.id
                WHERE j.id = ? AND j.owner_id = ?
            ''', (job_id, owner_id))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    @staticmethod
    def retry_job(job_id: int) -> bool:
        """Resetea un job fallido a estado pendiente para ser re-procesado."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE batch_jobs SET status='pending', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (job_id,)
            )
            conn.commit()
            return cursor.rowcount > 1

    @staticmethod
    def get_leads_for_job(job_id: int, owner_id: str) -> List[dict]:
        """Obtiene los leads reales de la DB de leads que coinciden con la zona/categoría del job."""
        job = StorageService.get_job_by_id(job_id, owner_id)
        if not job:
            return []
            
        city_name = job['city_name']
        cat_name = job['category_name']
        # GoogleMapsScraper guarda la zona como "Categoría en Ciudad"
        search_query = f"{cat_name} en {city_name}"
        
        if not os.path.exists(LEADS_DB_PATH):
            return []
            
        with sqlite3.connect(LEADS_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Filtramos por zona (que es el search_query)
            cursor.execute("SELECT * FROM leads WHERE zone = ?", (search_query,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def create_hybrid_job(owner_id: str, category_id: int = None, categoria_text: str = None, city_id: int = None, zona_text: str = None) -> int:
        """
        Punto de entrada unificado para crear Jobs. 
        Soporta tanto Jobs 100% relacionales (Frontend) como Jobs híbridos/texto-libre (Bot).
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO batch_jobs 
                (category_id, categoria_text, city_id, zona_text, owner_id, status) 
                VALUES (?, ?, ?, ?, ?, 'pending')
                """,
                (category_id, categoria_text, city_id, zona_text, owner_id)
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def create_batch_jobs(jobs_payloads: List[tuple]) -> int:
        """
        Inserta múltiples trabajos de forma atómica usando executemany.
        jobs_payloads debe ser lista de tuplas: 
        (category_id, categoria_text, city_id, zona_text, owner_id)
        """
        if not jobs_payloads:
            return 0
            
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT INTO batch_jobs 
                (category_id, categoria_text, city_id, zona_text, owner_id, status) 
                VALUES (?, ?, ?, ?, ?, 'pending')
                """,
                jobs_payloads
            )
            conn.commit()
            return cursor.rowcount
            
    @staticmethod
    def get_pending_job():
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE batch_jobs 
                SET status='processing', updated_at=CURRENT_TIMESTAMP
                WHERE id = (
                    SELECT id FROM batch_jobs 
                    WHERE status='pending' 
                    ORDER BY created_at ASC 
                    LIMIT 1
                )
                RETURNING id;
            ''')
            row = cursor.fetchone()
            if not row:
                return None
            
            job_id = row['id']
            # Dual-path: LEFT JOIN para soportar jobs del Bot (sin FK) y del Frontend (con FK)
            cursor.execute('''
                SELECT 
                    j.*,
                    c.name as category_name,
                    m.name as city_name,
                    j.zona_text,
                    j.categoria_text
                FROM batch_jobs j
                LEFT JOIN master_categories c ON j.category_id = c.id
                LEFT JOIN master_cities m ON j.city_id = m.id
                WHERE j.id=?
            ''', (job_id,))
            full_row = cursor.fetchone()
            return dict(full_row) if full_row else None

    @staticmethod
    def get_worker_enabled() -> bool:
        with sqlite3.connect(StorageService.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM worker_config WHERE key = 'is_enabled'")
            row = cursor.fetchone()
            if not row:
                return True # Default to enabled if not set
            return row[0].lower() == 'true'

    @staticmethod
    def set_worker_enabled(enabled: bool):
        value = 'true' if enabled else 'false'
        with sqlite3.connect(StorageService.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO worker_config (key, value) 
                VALUES ('is_enabled', ?)
                ON CONFLICT(key) DO UPDATE SET value=?
            ''', (value, value))
            conn.commit()

    @staticmethod
    def update_job_status(job_id: int, status: str):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE batch_jobs SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, job_id))
            conn.commit()

    @staticmethod
    def set_worker_heartbeat():
        """Actualiza el timestamp del worker para monitoreo de salud."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO worker_config (key, value) VALUES ('last_heartbeat', CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value=CURRENT_TIMESTAMP
            ''')
            conn.commit()

    @staticmethod
    def get_worker_health() -> dict:
        """Calcula el estado del worker basado en el último heartbeat."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM worker_config WHERE key = 'last_heartbeat'")
            row = cursor.fetchone()
            if not row:
                return {"status": "offline", "last_heartbeat": None}
            
            # Simple check: si el heartbeat es de hace más de 1 minuto, está offline
            # SQLite CURRENT_TIMESTAMP está en UTC.
            cursor.execute("SELECT (strftime('%s', 'now') - strftime('%s', value)) < 60 FROM worker_config WHERE key = 'last_heartbeat'")
            is_recent = cursor.fetchone()[0]
            
            # El estado es 'online' solo si hay latido RECIENTE y el switch está ACTIVADO
            is_enabled = StorageService.get_worker_enabled()
            
            return {
                "status": "online" if (is_recent and is_enabled) else "offline",
                "last_heartbeat": row[0]
            }


# Puedes usar estas funciones simples importándolas directamente
def buscar_excels_de_usuario(session_id: str) -> List[str]:
    return StorageService.fetch_excel_files_for_session(session_id)

def obtener_ruta_directorio(session_id: str) -> str:
    return StorageService.get_session_directory(session_id)
