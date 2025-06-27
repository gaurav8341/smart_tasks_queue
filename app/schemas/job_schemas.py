from pydantic import BaseModel, Field
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime, timezone
from enum import IntEnum

class PriorityEnum(IntEnum):
    Critical = 1
    High = 2
    Normal = 3
    Low = 4

class ResourceRequirements(BaseModel):
    cpu_units: Optional[int]
    memory_mb: Optional[int]

class RetryConfig(BaseModel):
    max_attempts: Optional[int] = 1
    backoff_multiplier: Optional[float] = 1.0
    initial_delay_seconds: Optional[int] = 0

class JobCreate(BaseModel):
    job_id: UUID
    job_name: str
    type: Optional[str]
    payload: Optional[Any]
    resource_requirements: Optional[ResourceRequirements] = None
    retry_config: Optional[RetryConfig] = None
    priority: PriorityEnum = PriorityEnum.Normal
    run_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    depends_on: Optional[List[UUID]] = []

class JobOut(BaseModel):
    job_id: UUID
    job_name: str
    type: Optional[str]
    payload: Optional[Any]
    status: str
    priority: PriorityEnum
    times_attempted: Optional[int]
    run_at: Optional[datetime]
    results: Optional[Any]
    resource_requirements: Optional[ResourceRequirements] = None
    retry_config: Optional[RetryConfig] = None
    depends_on: Optional[List[UUID]] = []

    class Config:
        orm_mode = True

class JobLogOut(BaseModel):
    id: int
    job_id: UUID
    duration_seconds: Optional[float]
    is_successful: Optional[bool]
    results: Optional[Any]
    execution_start_time: Optional[datetime]
    execution_end_time: Optional[datetime]
    message: Optional[str]
    status: Optional[str]
    resource_requirements: Optional[ResourceRequirements] = None

    class Config:
        orm_mode = True

class ExecutionLogOut(BaseModel):
    id: int
    job_id: int
    job_uuid: UUID
    log_timestamp: datetime
    message: str
    duration_seconds: Optional[float]
    is_successful: Optional[bool]
    results: Optional[Any]
    execution_start_time: Optional[datetime]
    execution_end_time: Optional[datetime]
    attempt_number: int
    resource_requirements: Optional[ResourceRequirements] = None

    class Config:
        orm_mode = True
