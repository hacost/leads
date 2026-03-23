from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from src.presentation.api.auth import get_current_user
from src.infrastructure.database.storage_service import StorageService

router = APIRouter(prefix="/api/leads", tags=["Leads"])

class LeadView(BaseModel):
    name: str
    phone: Optional[str] = "N/A"
    address: Optional[str] = "N/A"
    website: Optional[str] = "N/A"
    stars: float = 0.0
    reviews: int = 0
    map_url: Optional[str] = None

@router.get("/{job_id}", response_model=List[LeadView])
async def get_leads_by_job(job_id: int, current_user: dict = Depends(get_current_user)):
    """
    Returns the real leads extracted for a specific batch job.
    """
    owner_id = current_user.get("sub")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    leads = StorageService.get_leads_for_job(job_id, owner_id)
    return [LeadView(**l) for l in leads]
