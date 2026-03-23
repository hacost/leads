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
