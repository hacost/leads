from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.presentation.api.auth import get_current_user
from src.infrastructure.database.storage_service import StorageService

router = APIRouter(prefix="/api/admin", tags=["Admin Worker Switch"])

class WorkerToggle(BaseModel):
    is_enabled: bool

@router.get("/worker")
async def get_worker_status(current_user: dict = Depends(get_current_user)):
    return {"is_enabled": StorageService.get_worker_enabled()}

@router.patch("/worker")
async def set_worker_status(payload: WorkerToggle, current_user: dict = Depends(get_current_user)):
    StorageService.set_worker_enabled(payload.is_enabled)
    return {"is_enabled": payload.is_enabled, "message": "Worker configuration updated"}
