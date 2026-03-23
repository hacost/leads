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
    category_name: Optional[str] = "Unknown"
    city_name: Optional[str] = "Unknown"

@router.get("", response_model=List[BatchJobView])
async def get_jobs(
    limit: int = 50, 
    offset: int = 0, 
    current_user: dict = Depends(get_current_user)
):
    """
    Returns batch jobs scoped to the currently authenticated tenant with pagination.
    """
    owner_id = current_user.get("sub")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    jobs_dict = StorageService.get_jobs(owner_id=owner_id, limit=limit, offset=offset)
    return [BatchJobView(**job) for job in jobs_dict]

@router.get("/{job_id}", response_model=BatchJobView)
async def get_job(job_id: int, current_user: dict = Depends(get_current_user)):
    """
    Returns details for a specific batch job.
    """
    owner_id = current_user.get("sub")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    job_dict = StorageService.get_job_by_id(job_id=job_id, owner_id=owner_id)
    if not job_dict:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return BatchJobView(**job_dict)

@router.patch("/{job_id}/retry")
async def retry_job(job_id: int, current_user: dict = Depends(get_current_user)):
    """
    Resets a failed job to pending status.
    """
    owner_id = current_user.get("sub")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    # Primero verificamos que el job le pertenezca al usuario
    job = StorageService.get_job_by_id(job_id, owner_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or unauthorized")
        
    success = StorageService.retry_job(job_id)
    if not success:
        return {"message": "Job rescheduled for processing"} # Si rowcount fue 0 es porque ya estaba pending o no cambió
    
    return {"message": "Job rescheduled for processing"}

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
