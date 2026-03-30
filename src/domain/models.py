from pydantic import BaseModel, ConfigDict
from typing import Optional
from enum import Enum
from datetime import datetime

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class MasterCountry(BaseModel):
    id: Optional[int] = None
    name: str
    status: int = 1

    model_config = ConfigDict(from_attributes=True)

class MasterState(BaseModel):
    id: Optional[int] = None
    name: str
    country_id: int
    status: int = 1

    model_config = ConfigDict(from_attributes=True)

class MasterCity(BaseModel):
    id: Optional[int] = None
    name: str
    state_id: Optional[int] = None
    status: int = 1
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class MasterCityResponse(MasterCity):
    """
    Submodelo usado exclusivamente para devolver respuestas HTTP al frontend,
    adjuntando los nombres de los niveles jerárquicos superiores resueltos por JOINs.
    """
    state_name: Optional[str] = None
    country_name: Optional[str] = None

class MasterCategory(BaseModel):
    id: Optional[int] = None
    name: str
    status: int = 1

    model_config = ConfigDict(from_attributes=True)

class BatchJob(BaseModel):
    id: Optional[int] = None
    category_id: Optional[int] = None
    city_id: Optional[int] = None
    categoria_text: Optional[str] = None
    zona_text: Optional[str] = None
    owner_id: str
    status: JobStatus = JobStatus.PENDING
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
