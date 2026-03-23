import sqlite3
import pytest
from unittest.mock import patch
from src.infrastructure.database.storage_service import StorageService

import os
import tempfile

@pytest.fixture(autouse=True)
def clean_db():
    """Limpia las tablas antes y después de cada prueba usando una BD temporal"""
    fd, temp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    with patch("src.infrastructure.database.storage_service.DB_PATH", temp_path):
        from src.infrastructure.database.storage_service import _init_db
        _init_db()  # Recrea esquemas en el archivo vacío
        yield
        
    if os.path.exists(temp_path):
        os.remove(temp_path)

class TestStorageServiceTDD:
    def test_get_or_create_city_creates_new_city(self):
        """Si la ciudad no existe, debe crearla y devolver el nuevo ID."""
        city_id = StorageService.get_or_create_city("Nueva_Ciudad")
        assert city_id > 0
        
        # Verificar que se insertó correctamente
        with sqlite3.connect(StorageService.get_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM master_cities WHERE id=?", (city_id,))
            row = cursor.fetchone()
            assert row is not None
            assert row['name'] == "Nueva_Ciudad"
            assert row['state'] == "N/A"
            assert row['country'] == "N/A"

    def test_get_or_create_city_returns_existing(self):
        """Si la ciudad ya existe (sin importar mayúsculas), debe devolver el ID existente y no duplicar."""
        # Insertamos manualmente
        with sqlite3.connect(StorageService.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO master_cities (name, state, country) VALUES (?, ?, ?)", ("San Pedro", "NL", "Mexico"))
            conn.commit()
            original_id = cursor.lastrowid
            
        # Llamamos al método
        city_id = StorageService.get_or_create_city("san pedro") # Diferente casing
        
        assert city_id == original_id
        
        # Verificar que no hay duplicados
        with sqlite3.connect(StorageService.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM master_cities WHERE name COLLATE NOCASE = ?", ("san pedro",))
            assert cursor.fetchone()[0] == 1

    def test_get_or_create_category_creates_new(self):
        """Si la categoría no existe para el usuario, debe crearla."""
        category_id = StorageService.get_or_create_category("Dentistas", "user_123")
        assert category_id > 0
        
        with sqlite3.connect(StorageService.get_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tenant_categories WHERE id=?", (category_id,))
            row = cursor.fetchone()
            assert row is not None
            assert row['name'] == "Dentistas"
            assert row['owner_id'] == "user_123"

    def test_get_or_create_category_returns_existing(self):
        """Si la categoría ya existe para un usuario, devuelve su ID sin duplicar."""
        # Creamos una original
        original_id = StorageService.create_category("Plomeros", "user_456")
        
        # Intentamos recrear
        new_id = StorageService.get_or_create_category("plomeros", "user_456")
        
        assert new_id == original_id
        
        # Verificar que si es de otro owner, SI crea una nueva
        other_owner_id = StorageService.get_or_create_category("plomeros", "user_999")
        assert other_owner_id != original_id

    @patch("builtins.print")
    @patch("os.path.exists")
    @patch("shutil.rmtree")
    def test_eliminar_sesion_no_tiene_print_duplicado(self, mock_rmtree, mock_exists, mock_print):
        """Verifica que eliminar_sesion() no genere output duplicado."""
        mock_exists.return_value = True
        StorageService.eliminar_sesion("test_session_123")
        assert mock_print.call_count == 1, "El print se llamó múltiples veces de manera duplicada."

    def test_get_pending_job_es_atomico(self):
        """Verifica que get_pending_job() obtiene y actualiza el estado en una sola operación atómica."""
        import tempfile
        import os
        from src.infrastructure.database.storage_service import _init_db
        
        fd, temp_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        try:
            with patch("src.infrastructure.database.storage_service.DB_PATH", temp_path):
                # DDL
                _init_db()
                
                # Insert database state
                with sqlite3.connect(temp_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO master_cities (id, name, state, country) VALUES (10, 'City', 'State', 'Country')")
                    cursor.execute("INSERT INTO tenant_categories (id, name, owner_id) VALUES (10, 'Category', 'owner')")
                    cursor.execute("INSERT INTO batch_jobs (id, category_id, city_id, owner_id, status) VALUES (1, 10, 10, 'owner', 'pending')")
                    cursor.execute("INSERT INTO batch_jobs (id, category_id, city_id, owner_id, status) VALUES (2, 10, 10, 'owner', 'pending')")
                    conn.commit()
                
                # Call the method
                job = StorageService.get_pending_job()
                assert job is not None, "El job recuperado es None, probablemente falló la inserción MOCK"
                
                assert 'id' in job, f"job no contiene 'id'. Contenido: {job}"
                assert job['id'] == 1
                
                # Verifies the current status in DB
                with sqlite3.connect(temp_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT status FROM batch_jobs WHERE id=1")
                    status1 = cursor.fetchone()[0]
                    assert status1 == 'processing', f"Se esperaba 'processing' de forma atómica, pero se encontró '{status1}'"
                    
                    # Validate that the second job is untouched
                    cursor.execute("SELECT status FROM batch_jobs WHERE id=2")
                    status2 = cursor.fetchone()[0]
                    assert status2 == 'pending', f"El job secundario se modificó a '{status2}'"
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_heartbeat_persistence(self):
        """Llamar a set_worker_heartbeat() debe persistir el valor en worker_config."""
        StorageService.set_worker_heartbeat()
        
        with sqlite3.connect(StorageService.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM worker_config WHERE key = 'last_heartbeat'")
            row = cursor.fetchone()
            assert row is not None
            assert len(row[0]) > 0 # Debe tener un timestamp

    def test_get_job_by_id_with_joins(self):
        """get_job_by_id debe traer los nombres de categoría y ciudad mediante JOINs."""
        # Setup data
        with sqlite3.connect(StorageService.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO master_cities (name, state, country) VALUES ('Veracruz', 'VER', 'Mexico')")
            city_id = cursor.lastrowid
            cursor.execute("INSERT INTO tenant_categories (name, owner_id) VALUES ('Hoteles', 'user_1')")
            cat_id = cursor.lastrowid
            cursor.execute("INSERT INTO batch_jobs (category_id, city_id, owner_id, status) VALUES (?, ?, 'user_1', 'pending')", (cat_id, city_id))
            job_id = cursor.lastrowid
        
        job = StorageService.get_job_by_id(job_id, "user_1")
        assert job is not None
        assert job['city_name'] == "Veracruz"
        assert job['category_name'] == "Hoteles"

    def test_get_jobs_with_offset_pagination(self):
        """get_jobs con offset=1 debe saltarse el primer (más reciente) job."""
        with sqlite3.connect(StorageService.get_db_path()) as conn:
            cursor = conn.cursor()
            # Setup mandatory cities and categories for the JOIN to work (letting DB choose IDs)
            cursor.execute("INSERT INTO master_cities (name, state, country) VALUES ('C1', 'S1', 'MX')")
            city_id = cursor.lastrowid
            cursor.execute("INSERT INTO tenant_categories (name, owner_id) VALUES ('Cat1', 'u1')")
            cat_id = cursor.lastrowid
            # Insertar 2 jobs con diferentes timestamps manuales
            cursor.execute("INSERT INTO batch_jobs (category_id, city_id, owner_id, status, created_at) VALUES (?, ?, 'u1', 'pending', '2026-03-22 10:00:00')", (cat_id, city_id))
            cursor.execute("INSERT INTO batch_jobs (category_id, city_id, owner_id, status, created_at) VALUES (?, ?, 'u1', 'pending', '2026-03-22 11:00:00')", (cat_id, city_id)) # Más reciente
            conn.commit()
            
            # Recuperamos el ID del primer job insertado para la aserción
            cursor.execute("SELECT id FROM batch_jobs WHERE created_at = '2026-03-22 10:00:00'")
            first_job_id = cursor.fetchone()[0]
        
        # Con offset=1, el más reciente se ignora, queda el primero
        jobs = StorageService.get_jobs("u1", limit=1, offset=1)
        assert len(jobs) == 1
        assert jobs[0]['id'] == first_job_id

    def test_get_worker_health_logic(self):
        """get_worker_health debe devolver 'Offline' si el heartbeat es muy antiguo."""
        # Si no hay heartbeat, es offline
        health = StorageService.get_worker_health()
        assert health['status'] == 'offline'
        
        # Si hay un heartbeat de hace 1 hora, es offline
        with sqlite3.connect(StorageService.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO worker_config (key, value) VALUES ('last_heartbeat', '2000-01-01 00:00:00')")
            conn.commit()
            
        health = StorageService.get_worker_health()
        assert health['status'] == 'offline'
