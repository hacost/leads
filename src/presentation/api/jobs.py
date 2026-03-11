from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.presentation.api.auth import get_current_user
from src.domain.models import BatchJob, JobStatus
from src.infrastructure.database.storage_service import StorageService

router = APIRouter(prefix="/api/jobs", tags=["Batch Jobs"])

class JobCreate(BaseModel):
    category_id: int
    city_id: int

# We extend the BatchJob model to include the joined names for the UI
class BatchJobView(BatchJob):
    category_name: str
    city_name: str

@router.get("", response_model=List[BatchJobView])
async def get_jobs(current_user: dict = Depends(get_current_user)):
    """
    Returns batch jobs scoped to the currently authenticated tenant.
    """
    owner_id = current_user.get("sub")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    jobs_dict = StorageService.get_jobs(owner_id=owner_id)
    return [BatchJobView(**job) for job in jobs_dict]

@router.post("", response_model=BatchJob)
async def create_job(job: JobCreate, current_user: dict = Depends(get_current_user)):
    """
    Enqueues a new scraping job for a city and category.
    """
    owner_id = current_user.get("sub")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    job_id = StorageService.create_job(
        category_id=job.category_id, 
        city_id=job.city_id, 
        owner_id=owner_id
    )
    
    return BatchJob(
        id=job_id, 
        category_id=job.category_id, 
        city_id=job.city_id, 
        owner_id=owner_id,
        status=JobStatus.PENDING
    )
