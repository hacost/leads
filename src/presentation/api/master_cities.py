from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel

from src.domain.models import MasterCity
from src.infrastructure.database.storage_service import StorageService
from src.presentation.api.auth import get_current_user

router = APIRouter(prefix="/api/cities", tags=["Master Cities"])

@router.get("", response_model=List[MasterCity])
async def get_master_cities(current_user: dict = Depends(get_current_user)):
    """
    Returns the global catalog of Master Cities available for scraping.
    """
    cities_dict = StorageService.get_master_cities()
    return [MasterCity(**city) for city in cities_dict]

class CityCreate(BaseModel):
    name: str
    state: str
    country: str

@router.post("", status_code=201, response_model=MasterCity)
async def create_master_city(payload: CityCreate, current_user: dict = Depends(get_current_user)):
    """
    Creates a new master city in the global catalog. Only admins should theoretically do this.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can manage master cities")
    
    city_id = StorageService.create_master_city(name=payload.name, state=payload.state, country=payload.country)
    return MasterCity(id=city_id, name=payload.name, state=payload.state, country=payload.country)

@router.put("/{city_id}", response_model=MasterCity)
async def update_city(city_id: int, payload: CityCreate, current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can manage master cities")
    if StorageService.update_master_city(city_id, payload.name, payload.state, payload.country):
        return MasterCity(id=city_id, name=payload.name, state=payload.state, country=payload.country)
    raise HTTPException(status_code=404, detail="City not found")

@router.delete("/{city_id}", status_code=204)
async def delete_city(city_id: int, current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can manage master cities")
    if not StorageService.delete_master_city(city_id):
        raise HTTPException(status_code=404, detail="City not found")
