import sqlite3
import pytest
from src.infrastructure.database.storage_service import StorageService, _init_db


# ===========================================================================
# SPRINT 2 — Normalización de la Capa de Persistencia
# Estrategia: SQLite en memoria (:memory:) con conn_override.
# ESTADO OBJETIVO: ROJO — Ninguna de estas pruebas debe pasar aún.
# ===========================================================================


# ---------------------------------------------------------------------------
# Test 2.1 — La tabla 'countries' existe tras _init_db
# ---------------------------------------------------------------------------
def test_countries_table_is_created():
    conn = sqlite3.connect(":memory:")
    _init_db(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='master_countries'")
    assert cursor.fetchone() is not None


# ---------------------------------------------------------------------------
# Test 2.2 — La tabla 'states' existe tras _init_db
# ---------------------------------------------------------------------------
def test_states_table_is_created():
    conn = sqlite3.connect(":memory:")
    _init_db(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='master_states'")
    assert cursor.fetchone() is not None


# ---------------------------------------------------------------------------
# Test 2.3 — master_cities tiene 'state_id' y NO tiene 'state' ni 'country'
# ---------------------------------------------------------------------------
def test_master_cities_has_state_id_not_flat_strings():
    conn = sqlite3.connect(":memory:")
    _init_db(conn)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(master_cities)")
    cols = [row[1] for row in cursor.fetchall()]
    assert "state_id" in cols
    assert "state" not in cols
    assert "country" not in cols


# ---------------------------------------------------------------------------
# Test 2.4 — FK rechaza un state_id inválido (integridad referencial activa)
# ---------------------------------------------------------------------------
def test_fk_rejects_invalid_state_id():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    _init_db(conn)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO master_cities (name, state_id, status) VALUES (?,?,?)",
            ("X", 9999, 1),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Test 2.5 — create_country devuelve un ID entero positivo
# ---------------------------------------------------------------------------
def test_create_country_returns_id():
    conn = sqlite3.connect(":memory:")
    _init_db(conn)
    country_id = StorageService.create_country("Mexico", conn_override=conn)
    assert isinstance(country_id, int) and country_id > 0


# ---------------------------------------------------------------------------
# Test 2.6 — create_state vincula correctamente al country
# ---------------------------------------------------------------------------
def test_create_state_links_to_country():
    conn = sqlite3.connect(":memory:")
    _init_db(conn)
    cid = StorageService.create_country("Mexico", conn_override=conn)
    sid = StorageService.create_state("NL", cid, conn_override=conn)
    cursor = conn.cursor()
    cursor.execute("SELECT country_id FROM master_states WHERE id=?", (sid,))
    assert cursor.fetchone()[0] == cid


# ---------------------------------------------------------------------------
# Test 2.7 — create_master_city vincula correctamente al state
# ---------------------------------------------------------------------------
def test_create_city_links_to_state():
    conn = sqlite3.connect(":memory:")
    _init_db(conn)
    cid = StorageService.create_country("Mexico", conn_override=conn)
    sid = StorageService.create_state("NL", cid, conn_override=conn)
    city_id = StorageService.create_master_city("Monterrey", sid, conn_override=conn)
    cursor = conn.cursor()
    cursor.execute("SELECT state_id FROM master_cities WHERE id=?", (city_id,))
    assert cursor.fetchone()[0] == sid


# ---------------------------------------------------------------------------
# Test 2.8 — get_master_cities retorna state_name y country_name via JOIN
# ---------------------------------------------------------------------------
def test_get_cities_includes_state_and_country_name():
    conn = sqlite3.connect(":memory:")
    _init_db(conn)
    cid = StorageService.create_country("Mexico", conn_override=conn)
    sid = StorageService.create_state("NL", cid, conn_override=conn)
    StorageService.create_master_city("Monterrey", sid, conn_override=conn)
    cities = StorageService.get_master_cities(conn_override=conn)
    assert cities[0]["state_name"] == "NL"
    assert cities[0]["country_name"] == "Mexico"
