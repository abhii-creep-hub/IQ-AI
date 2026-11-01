from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.pipeline import PipelineListResponse, PipelineCandidate, PipelineHistoryItem, PipelineStageUpdate
from app.services.pipeline_service import PipelineService, PIPELINE_STAGES

router = APIRouter(prefix="/pipeline", tags=["Recruitment Pipeline"])


def _candidate_payload(candidate):
    return PipelineCandidate(
        id=candidate.id, name=candidate.name, email=candidate.email,
        job_id=candidate.job_id, job_title=candidate.job.title if candidate.job else None,
        rank=candidate.rank,
        ats_score=candidate.ats_result.total_score if candidate.ats_result else None,
        match_score=(candidate.ai_analysis.jd_match_score if candidate.ai_analysis.jd_match_score is not None
                     else candidate.ai_analysis.match_score)
        if candidate.ai_analysis else None,
        total_experience_years=candidate.total_experience_years,
        recruitment_stage=candidate.recruitment_stage, created_at=candidate.created_at,
    )


@router.get("/", response_model=PipelineListResponse)
async def list_pipeline(
    job_id: Optional[UUID] = None,
    unassigned: bool = False,
    search: Optional[str] = Query(None, max_length=200),
    stage: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if job_id and unassigned:
        raise HTTPException(status_code=400, detail="Choose a job or unassigned candidates, not both")
    if stage and stage not in PIPELINE_STAGES:
        raise HTTPException(status_code=400, detail="Invalid recruitment stage")
    result = await PipelineService(db).list_candidates(current_user.id, job_id, unassigned, search, stage)
    if result is None:
        raise HTTPException(status_code=404, detail="Job not found")
    candidates, counts = result
    return PipelineListResponse(candidates=[_candidate_payload(c) for c in candidates], stage_counts=counts)


@router.patch("/candidates/{candidate_id}/stage", response_model=PipelineCandidate)
async def update_pipeline_stage(
    candidate_id: UUID,
    data: PipelineStageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    candidate = await PipelineService(db).move_candidate(current_user, candidate_id, data.stage)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return _candidate_payload(candidate)


@router.get("/candidates/{candidate_id}/history", response_model=list[PipelineHistoryItem])
async def candidate_stage_history(
    candidate_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await PipelineService(db).history(current_user.id, candidate_id)
    if rows is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return [PipelineHistoryItem(
        id=log.id,
        previous_stage=(log.details or {}).get("previous_stage"),
        new_stage=(log.details or {}).get("new_stage", ""),
        created_at=log.created_at,
        recruiter=recruiter.full_name or recruiter.username,
    ) for log, recruiter in rows]
