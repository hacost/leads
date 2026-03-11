from fastapi import APIRouter
from typing import List

from src.domain.models import MasterCity
from src.infrastructure.database.storage_service import StorageService

router = APIRouter(prefix="/api/master-cities", tags=["Master Cities"])

@router.get("", response_model=List[MasterCity])
async def get_master_cities():
    """
    Returns the global catalog of Master Cities available for scraping.
    """
    cities_dict = StorageService.get_master_cities()
    return [MasterCity(**city) for city in cities_dict]
