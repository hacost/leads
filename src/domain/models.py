from pydantic import BaseModel, ConfigDict
from typing import Optional
from enum import Enum
from datetime import datetime

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class MasterCity(BaseModel):
    id: Optional[int] = None
    name: str
    state: str
    country: str
    status: int = 1
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TenantCategory(BaseModel):
    id: Optional[int] = None
    name: str
    owner_id: str
    status: int = 1

    model_config = ConfigDict(from_attributes=True)

class BatchJob(BaseModel):
    id: Optional[int] = None
    category_id: int
    city_id: int
    owner_id: str
    status: JobStatus = JobStatus.PENDING
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
