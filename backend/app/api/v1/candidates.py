from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database.session import get_db
from app.schemas.candidate import CandidateResponse, CandidateDetailResponse, ResumeUploadResponse
from app.services.candidate_service import CandidateService
from app.middleware.auth import get_current_user
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    job_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )
    service = CandidateService(db)
    parsed_job_id = UUID(job_id) if job_id else None
    try:
        result = await service.upload_resume(
            user_id=current_user.id,
            file_content=content,
            filename=file.filename,
            file_type=ext,
            job_id=parsed_job_id,
        )
        return ResumeUploadResponse(
            id=UUID(result["resume_id"]),
            filename=file.filename,
            status=result["status"],
            candidate_id=UUID(result["candidate_id"]),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-multiple", response_model=list[ResumeUploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_multiple_resumes(
    files: list[UploadFile] = File(...),
    job_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CandidateService(db)
    parsed_job_id = UUID(job_id) if job_id else None
    results = []
    for file in files:
        if not file.filename:
            continue
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in settings.allowed_extensions_list:
            continue
        content = await file.read()
        if len(content) > settings.max_upload_size_bytes:
            continue
        try:
            result = await service.upload_resume(
                user_id=current_user.id,
                file_content=content,
                filename=file.filename,
                file_type=ext,
                job_id=parsed_job_id,
            )
            results.append(ResumeUploadResponse(
                id=UUID(result["resume_id"]),
                filename=file.filename,
                status=result["status"],
                candidate_id=UUID(result["candidate_id"]),
            ))
        except Exception:
            continue
    return results


@router.get("/", response_model=list[CandidateResponse])
async def list_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    rank: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CandidateService(db)
    if search:
        candidates = await service.search_candidates(search)
    else:
        candidates = await service.list_candidates(skip, limit)
    if rank:
        candidates = [c for c in candidates if c.rank == rank]
    return candidates


@router.get("/{candidate_id}", response_model=CandidateDetailResponse)
async def get_candidate(
    candidate_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CandidateService(db)
    candidate = await service.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.put("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: UUID,
    name: Optional[str] = Query(None),
    rank: Optional[str] = Query(None),
    status_val: Optional[str] = Query(None, alias="status"),
    notes: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CandidateService(db)
    try:
        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if rank is not None:
            kwargs["rank"] = rank
        if status_val is not None:
            kwargs["status"] = status_val
        if notes is not None:
            kwargs["notes"] = notes
        candidate = await service.update_candidate(candidate_id, **kwargs)
        return candidate
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate(
    candidate_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CandidateService(db)
    deleted = await service.delete_candidate(candidate_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Candidate not found")


@router.post("/{candidate_id}/parse")
async def parse_resume(
    candidate_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CandidateService(db)
    try:
        result = await service.parse_resume(candidate_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")


@router.post("/{candidate_id}/analyze")
async def analyze_candidate(
    candidate_id: UUID,
    job_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CandidateService(db)
    try:
        parsed_job_id = UUID(job_id) if job_id else None
        result = await service.analyze_candidate(candidate_id, parsed_job_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/{candidate_id}/parse-and-analyze")
async def parse_and_analyze(
    candidate_id: UUID,
    job_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CandidateService(db)
    parsed_job_id = UUID(job_id) if job_id else None
    try:
        parse_result = await service.parse_resume(candidate_id)
        analysis_result = await service.analyze_candidate(candidate_id, parsed_job_id)
        return {
            "parse": parse_result,
            "analysis": analysis_result,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
