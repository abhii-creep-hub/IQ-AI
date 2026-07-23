from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class JobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    required_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    education_level: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    education_level: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    status: Optional[str] = None


class JobResponse(JobBase):
    id: UUID
    status: str
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    id: UUID
    title: str
    location: Optional[str] = None
    job_type: Optional[str] = None
    status: str
    required_skills: Optional[List[str]] = []
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    created_at: datetime
    candidate_count: Optional[int] = 0

    model_config = {"from_attributes": True}
