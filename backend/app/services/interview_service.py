from datetime import datetime, time, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.models.interview import Interview, InterviewFeedback
from app.models.log_report import ActivityLog


def candidate_access_clause(user_id: UUID):
    return or_(
        Candidate.job_id.in_(select(Job.id).where(Job.owner_id == user_id)),
        and_(Candidate.job_id.is_(None), Candidate.resume.has(Resume.uploaded_by == user_id)),
    )


class InterviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _load_options(self):
        return (
            selectinload(Interview.candidate),
            selectinload(Interview.job),
            selectinload(Interview.interviewer),
            selectinload(Interview.feedback).selectinload(InterviewFeedback.submitted_by),
        )

    async def _candidate(self, user_id: UUID, candidate_id: UUID):
        query = select(Candidate).options(selectinload(Candidate.job)).where(
            Candidate.id == candidate_id, candidate_access_clause(user_id)
        )
        return await self.db.scalar(query)

    async def _owned_job(self, user_id: UUID, job_id: UUID):
        return await self.db.scalar(select(Job).where(Job.id == job_id, Job.owner_id == user_id))

    async def _interviewer(self, interviewer_user_id: UUID | None):
        if interviewer_user_id is None:
            return None
        user = await self.db.scalar(select(User).where(User.id == interviewer_user_id, User.is_active.is_(True)))
        if user is None:
            raise LookupError("Interviewer was not found or is inactive")
        return user

    async def _candidate_owned(self, user_id: UUID, candidate_id: UUID) -> bool:
        return bool(await self.db.scalar(select(Candidate.id).where(
            Candidate.id == candidate_id, candidate_access_clause(user_id)
        )))

    async def _get_interview(self, user_id: UUID, interview_id: UUID):
        candidate_visible = candidate_access_clause(user_id)
        query = select(Interview).join(Candidate).options(*self._load_options()).where(
            Interview.id == interview_id,
            or_(candidate_visible, Interview.interviewer_user_id == user_id),
        )
        return await self.db.scalar(query)

    async def _commit(self):
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    def _log(self, user_id: UUID, interview: Interview, action: str, **details):
        self.db.add(ActivityLog(
            user_id=user_id, action=action, resource_type="interview",
            resource_id=interview.id, details=details or None,
        ))

    async def create(self, user: User, data: dict):
        scheduled_at = data["scheduled_at"]
        if scheduled_at.astimezone(timezone.utc) <= datetime.now(timezone.utc):
            raise ValueError("Interview must be scheduled for a future date and time")
        candidate = await self._candidate(user.id, data["candidate_id"])
        if candidate is None:
            raise LookupError("Candidate not found")

        selected_job_id = data.get("job_id") or candidate.job_id
        if candidate.job_id and selected_job_id != candidate.job_id:
            raise ValueError("Interview job must match the candidate's associated job")
        if selected_job_id and await self._owned_job(user.id, selected_job_id) is None:
            raise LookupError("Job not found")
        interviewer_id = data.get("interviewer_user_id")
        if interviewer_id is not None and interviewer_id != user.id:
            raise PermissionError("Interviews can only be assigned to your own account")
        interviewer = await self._interviewer(interviewer_id)
        if interviewer:
            data["interviewer_name"] = interviewer.full_name or interviewer.username
        data["scheduled_at"] = scheduled_at.astimezone(timezone.utc)
        interview_data = {key: value for key, value in data.items() if key not in ("candidate_id", "job_id")}
        interview = Interview(**interview_data, candidate_id=candidate.id, job_id=selected_job_id,
                              created_by_id=user.id, status="scheduled")
        self.db.add(interview)
        await self.db.flush()
        self._log(user.id, interview, "interview_scheduled", candidate_id=str(candidate.id), status="scheduled")
        await self._commit()
        return await self._get_interview(user.id, interview.id)

    async def list(self, user_id: UUID, *, search=None, status=None, job_id=None,
                   interview_type=None, from_date=None, to_date=None, candidate_id=None, timezone_name="UTC"):
        query = select(Interview).join(Candidate).options(*self._load_options()).where(
            or_(candidate_access_clause(user_id), Interview.interviewer_user_id == user_id)
        )
        if search:
            term = f"%{search.strip()}%"
            query = query.where(or_(Candidate.name.ilike(term), Candidate.email.ilike(term), Interview.interviewer_name.ilike(term)))
        if status:
            query = query.where(Interview.status == status)
        if job_id:
            if await self._owned_job(user_id, job_id) is None:
                raise LookupError("Job not found")
            query = query.where(Interview.job_id == job_id)
        if interview_type:
            query = query.where(Interview.interview_type == interview_type)
        if candidate_id:
            query = query.where(Interview.candidate_id == candidate_id)
        if from_date:
            start = datetime.combine(from_date, time.min, tzinfo=ZoneInfo(timezone_name)).astimezone(timezone.utc)
            query = query.where(Interview.scheduled_at >= start)
        if to_date:
            end = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=ZoneInfo(timezone_name)).astimezone(timezone.utc)
            query = query.where(Interview.scheduled_at < end)
        return list((await self.db.scalars(query.order_by(Interview.scheduled_at.asc()))).all())

    async def get(self, user_id: UUID, interview_id: UUID):
        interview = await self._get_interview(user_id, interview_id)
        if interview is None:
            raise LookupError("Interview not found")
        return interview

    async def update(self, user: User, interview_id: UUID, changes: dict):
        interview = await self.get(user.id, interview_id)
        if not await self._candidate_owned(user.id, interview.candidate_id) and interview.created_by_id != user.id:
            raise PermissionError("Only the recruiter who manages this candidate can change the interview")
        if interview.status not in ("scheduled", "rescheduled"):
            raise ValueError("Only scheduled interviews can be edited")
        if "scheduled_at" in changes:
            scheduled_at = changes["scheduled_at"]
            if scheduled_at.astimezone(timezone.utc) <= datetime.now(timezone.utc):
                raise ValueError("Rescheduled interview must be in the future")
            changes["scheduled_at"] = scheduled_at.astimezone(timezone.utc)
            interview.status = "rescheduled"
        if "job_id" in changes:
            if changes["job_id"] and await self._owned_job(user.id, changes["job_id"]) is None:
                raise LookupError("Job not found")
            candidate = interview.candidate
            if candidate.job_id and changes["job_id"] != candidate.job_id:
                raise ValueError("Interview job must match the candidate's associated job")
        if "interviewer_user_id" in changes:
            if changes["interviewer_user_id"] is not None and changes["interviewer_user_id"] != user.id:
                raise PermissionError("Interviews can only be assigned to your own account")
            await self._interviewer(changes["interviewer_user_id"])
        for field, value in changes.items():
            setattr(interview, field, value)
        self._log(user.id, interview, "interview_updated", status=interview.status,
                  scheduled_at=interview.scheduled_at.isoformat())
        await self._commit()
        return await self.get(user.id, interview_id)

    async def change_status(self, user: User, interview_id: UUID, status: str):
        interview = await self.get(user.id, interview_id)
        is_owner = await self._candidate_owned(user.id, interview.candidate_id) or interview.created_by_id == user.id
        is_assigned_interviewer = interview.interviewer_user_id == user.id
        if not is_owner and not (status == "completed" and is_assigned_interviewer):
            raise PermissionError("You cannot change this interview")
        if interview.status not in ("scheduled", "rescheduled"):
            raise ValueError("This interview can no longer be changed")
        interview.status = status
        self._log(user.id, interview, f"interview_{status}", status=status)
        await self._commit()
        return await self.get(user.id, interview_id)

    async def save_feedback(self, user: User, interview_id: UUID, data: dict):
        interview = await self.get(user.id, interview_id)
        if interview.interviewer_user_id:
            if interview.interviewer_user_id != user.id:
                raise PermissionError("Only the assigned interviewer can submit feedback")
        elif interview.created_by_id != user.id:
            raise PermissionError("Only the interview organizer can submit feedback")
        if interview.status != "completed":
            raise ValueError("Complete the interview before submitting feedback")
        feedback = interview.feedback
        if feedback is None:
            feedback = InterviewFeedback(interview_id=interview.id, submitted_by_id=user.id, **data)
            self.db.add(feedback)
        else:
            for field, value in data.items():
                setattr(feedback, field, value)
            feedback.submitted_by_id = user.id
        self._log(user.id, interview, "interview_feedback_submitted", recommendation=data["recommendation"])
        await self._commit()
        return await self.get(user.id, interview_id)
