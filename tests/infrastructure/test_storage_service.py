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
    def test_get_or_create_city_returns_none_if_not_in_catalog(self):
        """El catálogo es cerrado: si la ciudad no existe, devuelve None (ya no crea)."""
        result = StorageService.get_or_create_city("CiudadQueNoExiste")
        assert result is None

    def test_get_or_create_city_returns_existing_if_in_catalog(self):
        """Si la ciudad YA existe en el catálogo, devuelve su ID correctamente."""
        with sqlite3.connect(StorageService.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO master_countries (name) VALUES ('Mexico')")
            cursor.execute("SELECT id FROM master_countries WHERE name='Mexico'")
            mx_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO master_states (name, country_id) VALUES ('NL', ?)", (mx_id,))
            state_id = cursor.lastrowid
            cursor.execute("INSERT INTO master_cities (name, state_id) VALUES ('San Pedro', ?)", (state_id,))
            conn.commit()
            original_id = cursor.lastrowid

        city_id = StorageService.get_or_create_city("san pedro")  # Diferente casing
        assert city_id == original_id

        with sqlite3.connect(StorageService.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM master_cities WHERE name COLLATE NOCASE = ?", ("san pedro",))
            assert cursor.fetchone()[0] == 1

    def test_get_category_by_name_works(self):
        """Verifica que get_category_by_name devuelva la categoría maestra o None."""
        category_id = StorageService.create_category("Dentistas")
        assert category_id > 0
        
        cat = StorageService.get_category_by_name("Dentistas")
        assert cat is not None
        assert cat['name'] == "Dentistas"
        
        # Test missing
        missing = StorageService.get_category_by_name("Arquitectos")
        assert missing is None

    @patch("builtins.print")
    @patch("os.path.exists")
    @patch("shutil.rmtree")
    def test_eliminar_sesion_no_tiene_print_duplicado(self, mock_rmtree, mock_exists, mock_print):
        """Verifica que eliminar_sesion() no genere print() y que solo llame rmtree una vez."""
        mock_exists.return_value = True
        StorageService.eliminar_sesion("test_session_123")
        # El código usa logger.info, nunca print() directamente
        mock_print.assert_not_called()
        # El rmtree debe llamarse exactamente una vez (sin duplicados)
        mock_rmtree.assert_called_once()

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
                
                # Insert database state with normalized schema
                with sqlite3.connect(temp_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO master_countries (name) VALUES ('Country')")
                    country_id = cursor.lastrowid
                    cursor.execute("INSERT INTO master_states (name, country_id) VALUES ('State', ?)", (country_id,))
                    state_id = cursor.lastrowid
                    cursor.execute("INSERT INTO master_cities (id, name, state_id) VALUES (10, 'City', ?)", (state_id,))
                    cursor.execute("INSERT INTO master_categories (id, name) VALUES (10, 'Category')")
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
        # Setup data with normalized schema
        with sqlite3.connect(StorageService.get_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO master_countries (name) VALUES ('Mexico')")
            cursor.execute("SELECT id FROM master_countries WHERE name='Mexico'")
            mx_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO master_states (name, country_id) VALUES ('VER', ?)", (mx_id,))
            state_id = cursor.lastrowid
            cursor.execute("INSERT INTO master_cities (name, state_id) VALUES ('Veracruz', ?)", (state_id,))
            city_id = cursor.lastrowid
            cursor.execute("INSERT INTO master_categories (name) VALUES ('Hoteles')")
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
            # Setup with normalized schema
            cursor.execute("INSERT INTO master_countries (name) VALUES ('MX')")
            mx_id = cursor.lastrowid
            cursor.execute("INSERT INTO master_states (name, country_id) VALUES ('S1', ?)", (mx_id,))
            state_id = cursor.lastrowid
            cursor.execute("INSERT INTO master_cities (name, state_id) VALUES ('C1', ?)", (state_id,))
            city_id = cursor.lastrowid
            cursor.execute("INSERT INTO master_categories (name) VALUES ('Cat1')")
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
