from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel

from src.presentation.api.auth import get_current_user
from src.domain.models import MasterCategory
from src.infrastructure.database.storage_service import StorageService

router = APIRouter(prefix="/api/categories", tags=["Master Categories"])

class CategoryCreate(BaseModel):
    name: str

@router.get("", response_model=List[MasterCategory])
async def get_categories(limit: int = 100, offset: int = 0, current_user: dict = Depends(get_current_user)):
    """
    Returns categories from the global Master Catalog.
    """
    owner_id = current_user.get("sub")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    categories_dict = StorageService.get_categories()
    # Apply pagination in-memory for the global catalog
    return [MasterCategory(**cat) for cat in categories_dict[offset:offset+limit]]

@router.post("", response_model=MasterCategory)
async def create_category(category: CategoryCreate, current_user: dict = Depends(get_current_user)):
    """
    Creates a new global category.
    """
    owner_id = current_user.get("sub")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    cat_id = StorageService.create_category(name=category.name)
    return MasterCategory(id=cat_id, name=category.name)

@router.put("/{category_id}", response_model=MasterCategory)
async def update_category(category_id: int, payload: CategoryCreate, current_user: dict = Depends(get_current_user)):
    # Global categories shouldn't normally be updated by tenants
    owner_id = current_user.get("sub")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    raise HTTPException(status_code=403, detail="Master Categories cannot be renamed by tenants.")

@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: int, current_user: dict = Depends(get_current_user)):
    owner_id = current_user.get("sub")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Restrict delete for global catalogs
    raise HTTPException(status_code=403, detail="Master Categories cannot be deleted by tenants.")
