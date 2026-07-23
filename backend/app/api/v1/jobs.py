from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.job import JobCreate, JobUpdate, JobResponse, JobListResponse
from app.services.job_service import JobService
from app.services.candidate_service import CandidateService
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = JobService(db)
    try:
        job = await service.create_job(
            owner_id=current_user.id,
            title=data.title,
            description=data.description,
            requirements=data.requirements,
            responsibilities=data.responsibilities,
            required_skills=data.required_skills,
            preferred_skills=data.preferred_skills,
            experience_min=data.experience_min,
            experience_max=data.experience_max,
            education_level=data.education_level,
            location=data.location,
            job_type=data.job_type,
            salary_min=data.salary_min,
            salary_max=data.salary_max,
        )
        return job
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=list[JobListResponse])
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = JobService(db)
    if search:
        jobs = await service.search_jobs(search, current_user.id)
    else:
        jobs = await service.list_jobs(current_user.id, skip, limit)
    result = []
    for job in jobs:
        job_dict = {
            "id": job.id,
            "title": job.title,
            "location": job.location,
            "job_type": job.job_type,
            "status": job.status,
            "required_skills": job.required_skills or [],
            "experience_min": job.experience_min,
            "experience_max": job.experience_max,
            "created_at": job.created_at,
            "candidate_count": len(job.candidates) if hasattr(job, 'candidates') and job.candidates else 0,
        }
        result.append(JobListResponse(**job_dict))
    return result


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = JobService(db)
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: UUID,
    data: JobUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = JobService(db)
    try:
        update_data = data.model_dump(exclude_unset=True)
        job = await service.update_job(job_id, **update_data)
        return job
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = JobService(db)
    deleted = await service.delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")


@router.get("/{job_id}/candidates", response_model=list)
async def get_job_candidates(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CandidateService(db)
    candidates = await service.list_by_job(job_id)
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "email": c.email,
            "rank": c.rank,
            "status": c.status,
            "created_at": c.created_at.isoformat(),
        }
        for c in candidates
    ]
