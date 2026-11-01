from uuid import UUID
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.ai_interview import (
    AssistantCandidateOption, AssistantJobOption,
    AIAnswerUpdate, AIInterviewQuestionResponse, AIInterviewSessionResponse,
    AIInterviewSessionSummary, AISessionCreate, AISessionReviewUpdate,
)
from app.services.ai_interview_service import AIInterviewService, AIProviderError

router = APIRouter(prefix="/ai-interviews", tags=["AI Interview Assistant"])


@router.get("/candidates", response_model=list[AssistantCandidateOption])
async def list_assistant_candidates(
    search: str | None = Query(None, max_length=200),
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    candidates = await AIInterviewService(db).list_candidates(current_user.id, search=search, skip=skip, limit=limit)
    return [AssistantCandidateOption(
        id=candidate.id, name=candidate.name, email=candidate.email,
        job_id=candidate.job_id, job_title=candidate.job.title if candidate.job else None,
        rank=candidate.rank, summary=candidate.ai_summary,
        skills=[item.skill.name for item in (candidate.skills or []) if item.skill],
        experience_years=candidate.total_experience_years,
        ats_score=candidate.ats_result.total_score if candidate.ats_result else None,
    ) for candidate in candidates]


@router.get("/jobs", response_model=list[AssistantJobOption])
async def list_assistant_jobs(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    jobs = await AIInterviewService(db).list_jobs(current_user.id, skip=skip, limit=limit)
    return [AssistantJobOption(
        id=job.id, title=job.title, description=job.description,
        requirements=job.requirements, responsibilities=job.responsibilities,
        required_skills=job.required_skills or [], preferred_skills=job.preferred_skills or [],
        experience_min=job.experience_min, experience_max=job.experience_max,
    ) for job in jobs]


def _question_response(question):
    return AIInterviewQuestionResponse(
        id=question.id, order_index=question.order_index, question=question.question,
        parent_question_id=question.parent_question_id,
        category=question.category, difficulty=question.difficulty,
        competency=question.competency, job_relevance=question.job_relevance,
        expected_concepts=question.expected_concepts or [],
        evaluation_rubric=question.evaluation_rubric or {},
        follow_up_question=question.follow_up_question, answer=question.answer,
        evaluation=question.evaluation, score=question.score,
        answer_quality=question.answer_quality, status=question.status,
    )


def _session_response(session):
    candidate = session.candidate
    return AIInterviewSessionResponse(
        id=session.id, candidate_id=session.candidate_id,
        candidate_name=candidate.name if candidate else "Candidate unavailable",
        candidate_email=candidate.email if candidate else None,
        candidate_summary=candidate.ai_summary if candidate else None,
        candidate_skills=[item.skill.name for item in (candidate.skills or []) if item.skill] if candidate else [],
        candidate_experience_years=candidate.total_experience_years if candidate else None,
        ats_score=candidate.ats_result.total_score if candidate and candidate.ats_result else None,
        job_id=session.job_id, job_title=session.job.title if session.job else None,
        interview_type=session.interview_type, mode=session.mode or "written", difficulty=session.difficulty,
        question_count=session.question_count, duration_minutes=session.duration_minutes,
        status=session.status, created_at=session.created_at, completed_at=session.completed_at,
        questions=[_question_response(question) for question in (session.questions or [])],
        overall_report=session.overall_report, recruiter_notes=session.recruiter_notes,
        final_decision=session.final_decision,
    )


def _handle_error(error: Exception):
    if isinstance(error, AIProviderError):
        raise HTTPException(status_code=error.status_code, detail=str(error))
    if isinstance(error, LookupError):
        raise HTTPException(status_code=404, detail=str(error))
    if isinstance(error, PermissionError):
        raise HTTPException(status_code=403, detail=str(error))
    if isinstance(error, ValueError):
        raise HTTPException(status_code=400, detail=str(error))
    raise error


@router.post("/sessions", response_model=AIInterviewSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_interview_session(
    data: AISessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await AIInterviewService(db).create(current_user, data.model_dump())
        return _session_response(session)
    except (LookupError, PermissionError, ValueError, AIProviderError) as error:
        _handle_error(error)


@router.get("/sessions", response_model=list[AIInterviewSessionSummary])
async def list_ai_interview_sessions(
    candidate_id: UUID | None = None,
    job_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        sessions = await AIInterviewService(db).list(current_user.id, candidate_id=candidate_id, job_id=job_id)
        return [AIInterviewSessionSummary(
            id=session.id, candidate_id=session.candidate_id,
            candidate_name=session.candidate.name if session.candidate else "Candidate unavailable",
            job_id=session.job_id, job_title=session.job.title if session.job else None,
            interview_type=session.interview_type, difficulty=session.difficulty,
            mode=session.mode or "written",
            question_count=session.question_count, status=session.status,
            created_at=session.created_at, completed_at=session.completed_at,
        ) for session in sessions]
    except (LookupError, PermissionError, ValueError) as error:
        _handle_error(error)


@router.get("/sessions/{session_id}", response_model=AIInterviewSessionResponse)
async def get_ai_interview_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return _session_response(await AIInterviewService(db).get(current_user.id, session_id))
    except (LookupError, PermissionError, ValueError) as error:
        _handle_error(error)


@router.post("/sessions/{session_id}/generate", response_model=AIInterviewSessionResponse)
async def generate_session_questions(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return _session_response(await AIInterviewService(db).generate_questions(current_user.id, session_id))
    except (LookupError, PermissionError, ValueError, AIProviderError) as error:
        _handle_error(error)


@router.post("/sessions/{session_id}/start", response_model=AIInterviewSessionResponse)
async def start_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return _session_response(await AIInterviewService(db).start(current_user.id, session_id))
    except (LookupError, PermissionError, ValueError) as error:
        _handle_error(error)


@router.post("/sessions/{session_id}/pause", response_model=AIInterviewSessionResponse)
async def pause_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return _session_response(await AIInterviewService(db).pause(current_user.id, session_id))
    except (LookupError, PermissionError, ValueError) as error:
        _handle_error(error)


@router.put("/sessions/{session_id}/questions/{question_id}/answer", response_model=AIInterviewSessionResponse)
async def save_session_answer(
    session_id: UUID,
    question_id: UUID,
    data: AIAnswerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await AIInterviewService(db).save_answer(
            current_user.id, session_id, question_id,
            answer=data.answer, skip=data.skip,
        )
        return _session_response(session)
    except (LookupError, PermissionError, ValueError) as error:
        _handle_error(error)


@router.post("/sessions/{session_id}/questions/{question_id}/transcribe")
async def transcribe_session_answer(
    session_id: UUID,
    question_id: UUID,
    audio: UploadFile = File(...),
    duration_seconds: float = Form(ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mime_type = (audio.content_type or "").split(";")[0].strip().lower()
    allowed_audio_types = {"audio/webm", "audio/ogg", "audio/mp4", "audio/mpeg", "audio/wav", "audio/x-wav"}
    if mime_type not in allowed_audio_types:
        raise HTTPException(status_code=415, detail="Use a supported browser audio recording format (WebM, Ogg, MP4, MP3, or WAV).")
    if duration_seconds > settings.AI_AUDIO_MAX_SECONDS:
        raise HTTPException(status_code=413, detail=f"Recording must be {settings.AI_AUDIO_MAX_SECONDS} seconds or shorter.")
    try:
        audio_bytes = await audio.read(settings.AI_AUDIO_MAX_SIZE_MB * 1024 * 1024 + 1)
        if len(audio_bytes) > settings.AI_AUDIO_MAX_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"Recording must be {settings.AI_AUDIO_MAX_SIZE_MB} MB or smaller.")
        transcript = await AIInterviewService(db).transcribe_answer(
            current_user.id, session_id, question_id, audio_bytes, mime_type,
        )
        return transcript
    except HTTPException:
        raise
    except (LookupError, PermissionError, ValueError, AIProviderError) as error:
        _handle_error(error)


@router.post("/sessions/{session_id}/questions/{question_id}/live-follow-up", response_model=AIInterviewSessionResponse)
async def append_live_session_follow_up(
    session_id: UUID,
    question_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return _session_response(await AIInterviewService(db).append_live_follow_up(
            current_user.id, session_id, question_id,
        ))
    except (LookupError, PermissionError, ValueError, AIProviderError) as error:
        _handle_error(error)


@router.post("/sessions/{session_id}/questions/{question_id}/evaluate", response_model=AIInterviewSessionResponse)
async def evaluate_session_answer(
    session_id: UUID,
    question_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return _session_response(await AIInterviewService(db).evaluate_answer(current_user.id, session_id, question_id))
    except (LookupError, PermissionError, ValueError, AIProviderError) as error:
        _handle_error(error)


@router.post("/sessions/{session_id}/questions/{question_id}/follow-up", response_model=AIInterviewSessionResponse)
async def generate_session_follow_up(
    session_id: UUID,
    question_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return _session_response(await AIInterviewService(db).generate_follow_up(current_user.id, session_id, question_id))
    except (LookupError, PermissionError, ValueError, AIProviderError) as error:
        _handle_error(error)


@router.post("/sessions/{session_id}/complete", response_model=AIInterviewSessionResponse)
async def complete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return _session_response(await AIInterviewService(db).complete(current_user.id, session_id))
    except (LookupError, PermissionError, ValueError) as error:
        _handle_error(error)


@router.get("/sessions/{session_id}/report")
async def get_session_report(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        session, report = await AIInterviewService(db).report(current_user.id, session_id)
        return {
            "candidate": {"id": str(session.candidate_id), "name": session.candidate.name if session.candidate else None},
            "job": {"id": str(session.job_id) if session.job_id else None, "title": session.job.title if session.job else None},
            **report,
            "recruiter_notes": session.recruiter_notes,
            "final_decision": session.final_decision,
        }
    except (LookupError, PermissionError, ValueError) as error:
        _handle_error(error)


@router.patch("/sessions/{session_id}/review", response_model=AIInterviewSessionResponse)
async def update_session_review(
    session_id: UUID,
    data: AISessionReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await AIInterviewService(db).update_review(
            current_user.id, session_id, **data.model_dump(exclude_unset=True)
        )
        return _session_response(session)
    except (LookupError, PermissionError, ValueError) as error:
        _handle_error(error)
