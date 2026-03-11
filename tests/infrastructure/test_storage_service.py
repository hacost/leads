import sqlite3
import pytest
from unittest.mock import patch
from src.infrastructure.database.storage_service import StorageService, DB_PATH

@pytest.fixture(autouse=True)
def clean_db():
    """Limpia las tablas antes y después de cada prueba"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM master_cities")
        cursor.execute("DELETE FROM tenant_categories")
        conn.commit()
    yield
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM master_cities")
        cursor.execute("DELETE FROM tenant_categories")
        conn.commit()

class TestStorageServiceTDD:
    def test_get_or_create_city_creates_new_city(self):
        """Si la ciudad no existe, debe crearla y devolver el nuevo ID."""
        city_id = StorageService.get_or_create_city("Monterrey")
        assert city_id > 0
        
        # Verificar que se insertó correctamente
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM master_cities WHERE id=?", (city_id,))
            row = cursor.fetchone()
            assert row is not None
            assert row['name'] == "Monterrey"
            assert row['state'] == "N/A"
            assert row['country'] == "N/A"

    def test_get_or_create_city_returns_existing(self):
        """Si la ciudad ya existe (sin importar mayúsculas), debe devolver el ID existente y no duplicar."""
        # Insertamos manualmente
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO master_cities (name, state, country) VALUES (?, ?, ?)", ("San Pedro", "NL", "Mexico"))
            conn.commit()
            original_id = cursor.lastrowid
            
        # Llamamos al método
        city_id = StorageService.get_or_create_city("san pedro") # Diferente casing
        
        assert city_id == original_id
        
        # Verificar que no hay duplicados
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM master_cities WHERE name COLLATE NOCASE = ?", ("san pedro",))
            assert cursor.fetchone()[0] == 1

    def test_get_or_create_category_creates_new(self):
        """Si la categoría no existe para el usuario, debe crearla."""
        category_id = StorageService.get_or_create_category("Dentistas", "user_123")
        assert category_id > 0
        
        with sqlite3.connect(DB_PATH) as conn:
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
