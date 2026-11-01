from uuid import UUID
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.models.log_report import ActivityLog
from app.models.user import User

PIPELINE_STAGES = ("applied", "screening", "shortlisted", "interview", "offer", "hired", "rejected")


class PipelineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _owned_candidate_query(self, user_id: UUID):
        owned_job = Candidate.job_id.in_(select(Job.id).where(Job.owner_id == user_id))
        uploaded_unassigned = (Candidate.job_id.is_(None)) & Candidate.resume.has(Resume.uploaded_by == user_id)
        return select(Candidate).where(or_(owned_job, uploaded_unassigned))

    async def list_candidates(self, user_id: UUID, job_id: UUID | None = None, unassigned: bool = False,
                              search: str | None = None, stage: str | None = None):
        query = self._owned_candidate_query(user_id).options(
            selectinload(Candidate.job), selectinload(Candidate.ats_result),
            selectinload(Candidate.ai_analysis),
        )
        if job_id is not None:
            owned_job = await self.db.scalar(select(Job.id).where(Job.id == job_id, Job.owner_id == user_id))
            if owned_job is None:
                return None
            query = query.where(Candidate.job_id == job_id)
        elif unassigned:
            query = query.where(Candidate.job_id.is_(None))
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(or_(Candidate.name.ilike(pattern), Candidate.email.ilike(pattern)))
        if stage:
            query = query.where(Candidate.recruitment_stage == stage)
        query = query.order_by(Candidate.created_at.desc())
        candidates = list((await self.db.scalars(query)).all())
        counts = {name: 0 for name in PIPELINE_STAGES}
        for candidate in candidates:
            counts[candidate.recruitment_stage] = counts.get(candidate.recruitment_stage, 0) + 1
        return candidates, counts

    async def get_candidate(self, user_id: UUID, candidate_id: UUID):
        query = self._owned_candidate_query(user_id).options(
            selectinload(Candidate.job), selectinload(Candidate.ats_result), selectinload(Candidate.ai_analysis),
        ).where(Candidate.id == candidate_id)
        return await self.db.scalar(query)

    async def move_candidate(self, user: User, candidate_id: UUID, stage: str):
        if stage not in PIPELINE_STAGES:
            raise ValueError("Invalid recruitment stage")
        candidate = await self.get_candidate(user.id, candidate_id)
        if candidate is None:
            return None
        previous = candidate.recruitment_stage
        if previous == stage:
            return candidate
        candidate.recruitment_stage = stage
        self.db.add(ActivityLog(
            user_id=user.id, action="candidate_stage_changed", resource_type="candidate",
            resource_id=candidate.id,
            details={"previous_stage": previous, "new_stage": stage},
        ))
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        await self.db.refresh(candidate)
        return candidate

    async def history(self, user_id: UUID, candidate_id: UUID):
        if await self.get_candidate(user_id, candidate_id) is None:
            return None
        result = await self.db.execute(
            select(ActivityLog, User).join(User, User.id == ActivityLog.user_id)
            .where(ActivityLog.action == "candidate_stage_changed",
                   ActivityLog.resource_type == "candidate", ActivityLog.resource_id == candidate_id)
            .order_by(ActivityLog.created_at.desc())
        )
        return list(result.all())
