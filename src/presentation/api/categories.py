from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel

from src.presentation.api.auth import get_current_user
from src.domain.models import TenantCategory
from src.infrastructure.database.storage_service import StorageService

router = APIRouter(prefix="/api/categories", tags=["Tenant Categories"])

class CategoryCreate(BaseModel):
    name: str

@router.get("", response_model=List[TenantCategory])
async def get_categories(current_user: dict = Depends(get_current_user)):
    """
    Returns categories scoped to the currently authenticated tenant.
    """
    owner_id = current_user.get("sub")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    categories_dict = StorageService.get_categories(owner_id=owner_id)
    return [TenantCategory(**cat) for cat in categories_dict]

@router.post("", response_model=TenantCategory)
async def create_category(category: CategoryCreate, current_user: dict = Depends(get_current_user)):
    """
    Creates a new category for the currently authenticated tenant.
    """
    owner_id = current_user.get("sub")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    cat_id = StorageService.create_category(name=category.name, owner_id=owner_id)
    return TenantCategory(id=cat_id, name=category.name, owner_id=owner_id)
