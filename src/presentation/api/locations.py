from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel

from src.domain.models import MasterCountry, MasterState, MasterCity, MasterCityResponse
from src.infrastructure.database.storage_service import StorageService
from src.presentation.api.auth import get_current_user

router = APIRouter(tags=["Locations"])

# ---------------------------------------------------------------------------
# Schemas de entrada (solo admins los usan)
# ---------------------------------------------------------------------------

class CountryCreate(BaseModel):
    name: str

class StateCreate(BaseModel):
    name: str
    country_id: int

class CityCreate(BaseModel):
    name: str
    state_id: int

# ---------------------------------------------------------------------------
# Dependencia RBAC: solo administradores
# ---------------------------------------------------------------------------

def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return current_user

# ---------------------------------------------------------------------------
# /api/countries
# ---------------------------------------------------------------------------

@router.get("/api/countries", response_model=List[MasterCountry])
async def get_countries():
    """Retorna el catálogo global de países. Lectura pública."""
    return [MasterCountry(**c) for c in StorageService.get_countries()]


@router.post("/api/countries", response_model=MasterCountry, status_code=201)
async def create_country(payload: CountryCreate, current_user: dict = Depends(require_admin)):
    """Crea un nuevo país en el catálogo. Solo admins."""
    country_id = StorageService.create_country(name=payload.name)
    return MasterCountry(id=country_id, name=payload.name)

@router.put("/api/countries/{country_id}", response_model=MasterCountry)
async def update_country(country_id: int, payload: CountryCreate, current_user: dict = Depends(require_admin)):
    """Actualiza el nombre de un país. Solo admins."""
    if not StorageService.update_country(country_id, payload.name):
        raise HTTPException(status_code=404, detail="Country not found")
    return MasterCountry(id=country_id, name=payload.name)

# ---------------------------------------------------------------------------
# /api/states
# ---------------------------------------------------------------------------

@router.get("/api/states", response_model=List[MasterState])
async def get_states(country_id: int):
    """Retorna los estados de un país. Lectura pública."""
    return [MasterState(**s) for s in StorageService.get_states_by_country(country_id)]


@router.post("/api/states", response_model=MasterState, status_code=201)
async def create_state(payload: StateCreate, current_user: dict = Depends(require_admin)):
    """Crea un nuevo estado vinculado a un país. Solo admins."""
    state_id = StorageService.create_state(name=payload.name, country_id=payload.country_id)
    return MasterState(id=state_id, name=payload.name, country_id=payload.country_id)

@router.put("/api/states/{state_id}", response_model=MasterState)
async def update_state(state_id: int, payload: StateCreate, current_user: dict = Depends(require_admin)):
    """Actualiza un estado. Solo admins."""
    if not StorageService.update_state(state_id, payload.name):
        raise HTTPException(status_code=404, detail="State not found")
    return MasterState(id=state_id, name=payload.name, country_id=payload.country_id)

@router.delete("/api/states/{state_id}", status_code=204)
async def delete_state(state_id: int, current_user: dict = Depends(require_admin)):
    """Elimina lógicamente un estado y todas sus ciudades en cascada. Solo admins."""
    if not StorageService.delete_state_with_cascade(state_id):
        raise HTTPException(status_code=404, detail="State not found")

# ---------------------------------------------------------------------------
# /api/cities  (migrado desde master_cities.py)
# ---------------------------------------------------------------------------

@router.get("/api/cities", response_model=List[MasterCityResponse])
async def get_cities(
    state_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """Retorna el catálogo de ciudades con jerarquía. Lectura pública."""
    cities = StorageService.get_master_cities(limit=limit, offset=offset, state_id=state_id)
    return [MasterCityResponse(**c) for c in cities]


@router.post("/api/cities", response_model=MasterCity, status_code=201)
async def create_city(payload: CityCreate, current_user: dict = Depends(require_admin)):
    """Crea una nueva ciudad en el catálogo. Solo admins. Requiere state_id."""
    city_id = StorageService.create_master_city(name=payload.name, state_id=payload.state_id)
    return MasterCity(id=city_id, name=payload.name, state_id=payload.state_id)


@router.put("/api/cities/{city_id}", response_model=MasterCity)
async def update_city(city_id: int, payload: CityCreate, current_user: dict = Depends(require_admin)):
    """Actualiza una ciudad. Solo admins."""
    if not StorageService.update_master_city(city_id, payload.name, payload.state_id):
        raise HTTPException(status_code=404, detail="City not found")
    return MasterCity(id=city_id, name=payload.name, state_id=payload.state_id)


@router.delete("/api/cities/{city_id}", status_code=204)
async def delete_city(city_id: int, current_user: dict = Depends(require_admin)):
    """Elimina una ciudad del catálogo. Solo admins."""
    if not StorageService.delete_master_city(city_id):
        raise HTTPException(status_code=404, detail="City not found")
