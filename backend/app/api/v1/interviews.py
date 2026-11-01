from datetime import date
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.interview import (
    InterviewCreate, InterviewFeedbackCreate, InterviewFeedbackResponse,
    InterviewResponse, InterviewStatus, InterviewType, InterviewUpdate,
)
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interviews", tags=["Interviews"])


def _feedback_response(feedback):
    if feedback is None:
        return None
    return InterviewFeedbackResponse(
        id=feedback.id, skills_rating=feedback.skills_rating,
        communication_rating=feedback.communication_rating,
        problem_solving_rating=feedback.problem_solving_rating,
        overall_rating=feedback.overall_rating, recommendation=feedback.recommendation,
        notes=feedback.notes, submitted_by_id=feedback.submitted_by_id,
        submitted_by_name=(feedback.submitted_by.full_name or feedback.submitted_by.username)
        if feedback.submitted_by else None,
        updated_at=feedback.updated_at,
    )


def _response(interview):
    return InterviewResponse(
        id=interview.id, candidate_id=interview.candidate_id,
        candidate_name=interview.candidate.name if interview.candidate else "Deleted candidate",
        candidate_email=interview.candidate.email if interview.candidate else None,
        job_id=interview.job_id, job_title=interview.job.title if interview.job else None,
        interviewer_user_id=interview.interviewer_user_id, interviewer_name=interview.interviewer_name,
        interview_type=interview.interview_type, scheduled_at=interview.scheduled_at,
        timezone=interview.timezone, duration_minutes=interview.duration_minutes,
        location=interview.location, meeting_link=interview.meeting_link, notes=interview.notes,
        status=interview.status, created_by_id=interview.created_by_id,
        created_at=interview.created_at, updated_at=interview.updated_at,
        feedback=_feedback_response(interview.feedback),
    )


def _raise_service_error(error: Exception):
    if isinstance(error, LookupError):
        raise HTTPException(status_code=404, detail=str(error))
    if isinstance(error, PermissionError):
        raise HTTPException(status_code=403, detail=str(error))
    if isinstance(error, ValueError):
        raise HTTPException(status_code=400, detail=str(error))
    raise error


@router.post("/", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
async def schedule_interview(
    data: InterviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        interview = await InterviewService(db).create(current_user, data.model_dump())
        return _response(interview)
    except (ValueError, LookupError, PermissionError) as error:
        _raise_service_error(error)


@router.get("/", response_model=list[InterviewResponse])
async def list_interviews(
    search: str | None = Query(None, max_length=200),
    interview_status: InterviewStatus | None = Query(None, alias="status"),
    job_id: UUID | None = None,
    interview_type: InterviewType | None = None,
    candidate_id: UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    timezone_name: str = Query("UTC", alias="timezone", max_length=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="Start date must be on or before end date")
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as error:
        raise HTTPException(status_code=400, detail="Enter a valid IANA timezone") from error
    try:
        interviews = await InterviewService(db).list(
            current_user.id, search=search, status=interview_status, job_id=job_id,
            interview_type=interview_type, from_date=from_date, to_date=to_date,
            candidate_id=candidate_id,
            timezone_name=timezone_name,
        )
        return [_response(interview) for interview in interviews]
    except (ValueError, LookupError, PermissionError) as error:
        _raise_service_error(error)


@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return _response(await InterviewService(db).get(current_user.id, interview_id))
    except (ValueError, LookupError, PermissionError) as error:
        _raise_service_error(error)


@router.patch("/{interview_id}", response_model=InterviewResponse)
async def update_interview(
    interview_id: UUID,
    data: InterviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        interview = await InterviewService(db).update(current_user, interview_id, data.model_dump(exclude_unset=True))
        return _response(interview)
    except (ValueError, LookupError, PermissionError) as error:
        _raise_service_error(error)


@router.post("/{interview_id}/cancel", response_model=InterviewResponse)
async def cancel_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return _response(await InterviewService(db).change_status(current_user, interview_id, "cancelled"))
    except (ValueError, LookupError, PermissionError) as error:
        _raise_service_error(error)


@router.post("/{interview_id}/complete", response_model=InterviewResponse)
async def complete_interview(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return _response(await InterviewService(db).change_status(current_user, interview_id, "completed"))
    except (ValueError, LookupError, PermissionError) as error:
        _raise_service_error(error)


@router.put("/{interview_id}/feedback", response_model=InterviewResponse)
async def submit_interview_feedback(
    interview_id: UUID,
    data: InterviewFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return _response(await InterviewService(db).save_feedback(current_user, interview_id, data.model_dump()))
    except (ValueError, LookupError, PermissionError) as error:
        _raise_service_error(error)


@router.get("/{interview_id}/feedback", response_model=InterviewFeedbackResponse)
async def get_interview_feedback(
    interview_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        interview = await InterviewService(db).get(current_user.id, interview_id)
    except (ValueError, LookupError, PermissionError) as error:
        _raise_service_error(error)
    if not interview.feedback:
        raise HTTPException(status_code=404, detail="Feedback has not been submitted")
    return _feedback_response(interview.feedback)
