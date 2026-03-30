from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel, model_validator
from datetime import datetime

from src.presentation.api.auth import get_current_user
from src.domain.models import BatchJob, JobStatus
from src.infrastructure.database.storage_service import StorageService

router = APIRouter(prefix="/api/jobs", tags=["Batch Jobs"])

class JobCreate(BaseModel):
    category_id: Optional[int] = None
    city_id: Optional[int] = None
    categoria_text: Optional[str] = None
    zona_text: Optional[str] = None

    @model_validator(mode='after')
    def check_category_exists(self) -> 'JobCreate':
        if not self.category_id and not self.categoria_text:
            raise ValueError("Debe proporcionar al menos un ID de categoría o un texto de categoría libre.")
        return self

# We extend the BatchJob model to include the joined names for the UI
class BatchJobView(BatchJob):
    category_name: Optional[str] = "Unknown"
    city_name: Optional[str] = "Unknown"

    @model_validator(mode='after')
    def resolve_hybrid_names(self):
        """
        Si los nombres resueltos por JOIN son nulos o 'Unknown' (porque el Job no usa 
        el catálogo maestro), usamos los campos de texto libre para que el Dashboard 
        muestre algo útil.
        """
        if not self.category_name or self.category_name == "Unknown":
            if self.categoria_text:
                self.category_name = self.categoria_text
        
        if not self.city_name or self.city_name == "Unknown":
            if self.zona_text:
                self.city_name = self.zona_text
                
        return self

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
        
    job_id = StorageService.create_hybrid_job(
        category_id=job.category_id, 
        categoria_text=job.categoria_text,
        city_id=job.city_id,
        zona_text=job.zona_text,
        owner_id=owner_id
    )
    
    return BatchJob(
        id=job_id, 
        category_id=job.category_id, 
        categoria_text=job.categoria_text,
        city_id=job.city_id, 
        zona_text=job.zona_text,
        owner_id=owner_id,
        status=JobStatus.PENDING
    )

class BatchCreate(BaseModel):
    category_id: int
    city_id: Optional[int] = None
    state_id: Optional[int] = None
    all_cities: Optional[bool] = False
    max_leads: Optional[int] = 50

@router.post("/batch", status_code=201)
async def create_batch_jobs(payload: BatchCreate, current_user: dict = Depends(get_current_user)):
    """
    Creates multiple scraping jobs at once for a given category across multiple cities.
    """
    owner_id = current_user.get("sub")
    if not owner_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not payload.city_id and not payload.state_id and not payload.all_cities:
        raise HTTPException(status_code=400, detail="Must specify city_id, state_id, or all_cities=true")

    target_cities = []
    if payload.all_cities:
        target_cities = StorageService.get_master_cities(limit=10000)
    elif payload.state_id:
        target_cities = StorageService.get_master_cities(limit=10000, state_id=payload.state_id)
    elif payload.city_id:
        target_cities = [{"id": payload.city_id}]

    if not target_cities:
        raise HTTPException(status_code=404, detail="No target cities found")

    jobs_payloads = [
        (payload.category_id, None, city["id"], None, owner_id)
        for city in target_cities
    ]

    count = StorageService.create_batch_jobs(jobs_payloads)
    
    return {"message": f"{count} Jobs Enqueued successfully in batch"}
