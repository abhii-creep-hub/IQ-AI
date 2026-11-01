from datetime import datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel

PipelineStage = Literal["applied", "screening", "shortlisted", "interview", "offer", "hired", "rejected"]


class PipelineStageUpdate(BaseModel):
    stage: PipelineStage


class PipelineCandidate(BaseModel):
    id: UUID
    name: str
    email: Optional[str] = None
    job_id: Optional[UUID] = None
    job_title: Optional[str] = None
    rank: Optional[str] = None
    ats_score: Optional[float] = None
    match_score: Optional[float] = None
    total_experience_years: Optional[float] = None
    recruitment_stage: PipelineStage
    created_at: datetime

    model_config = {"from_attributes": True}


class PipelineListResponse(BaseModel):
    candidates: list[PipelineCandidate]
    stage_counts: dict[str, int]


class PipelineHistoryItem(BaseModel):
    id: UUID
    previous_stage: Optional[str] = None
    new_stage: str
    created_at: datetime
    recruiter: Optional[str] = None
