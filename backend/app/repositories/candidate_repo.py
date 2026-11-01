from typing import Optional
from uuid import UUID
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.candidate import Candidate
from app.models.resume import Resume
from app.models.skill import Skill, CandidateSkill
from app.models.education_experience import Education, Experience, Project, Certification
from app.models.analysis import ATSResult, AIAnalysis, InterviewQuestion


class CandidateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, candidate_id: UUID) -> Optional[Candidate]:
        result = await self.db.execute(
            select(Candidate)
            .options(
                selectinload(Candidate.resume),
                selectinload(Candidate.skills).selectinload(CandidateSkill.skill),
                selectinload(Candidate.education),
                selectinload(Candidate.experience),
                selectinload(Candidate.projects),
                selectinload(Candidate.certifications),
                selectinload(Candidate.ats_result),
                selectinload(Candidate.ai_analysis),
            )
            .where(Candidate.id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def create(self, candidate: Candidate) -> Candidate:
        self.db.add(candidate)
        await self.db.commit()
        await self.db.refresh(candidate)
        return candidate

    async def update(self, candidate: Candidate) -> Candidate:
        await self.db.commit()
        await self.db.refresh(candidate)
        return candidate

    async def delete(self, candidate_id: UUID) -> bool:
        candidate = await self.get_by_id(candidate_id)
        if candidate:
            await self.db.delete(candidate)
            await self.db.commit()
            return True
        return False

    async def list_by_job(self, job_id: UUID, skip: int = 0, limit: int = 100) -> list[Candidate]:
        result = await self.db.execute(
            select(Candidate)
            .where(Candidate.job_id == job_id)
            .offset(skip)
            .limit(limit)
            .order_by(Candidate.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[Candidate]:
        result = await self.db.execute(
            select(Candidate).offset(skip).limit(limit).order_by(Candidate.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_with_relations(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        rank: Optional[str] = None,
        job_id: Optional[UUID] = None,
        unassigned: bool = False,
    ) -> list[Candidate]:
        query = select(Candidate).options(
            selectinload(Candidate.skills).selectinload(CandidateSkill.skill),
            selectinload(Candidate.resume),
            selectinload(Candidate.ats_result),
        )
        if search:
            query = query.where(
                or_(
                    Candidate.name.ilike(f"%{search}%"),
                    Candidate.email.ilike(f"%{search}%"),
                    Candidate.location.ilike(f"%{search}%"),
                )
            )
        if rank:
            query = query.where(Candidate.rank == rank)
        if unassigned:
            query = query.where(Candidate.job_id.is_(None))
        elif job_id:
            query = query.where(Candidate.job_id == job_id)

        result = await self.db.execute(
            query
            .offset(skip)
            .limit(limit)
            .order_by(Candidate.created_at.desc())
        )
        return list(result.scalars().all())

    async def count(self, job_id: Optional[UUID] = None) -> int:
        query = select(func.count(Candidate.id))
        if job_id:
            query = query.where(Candidate.job_id == job_id)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def search(self, query_str: str) -> list[Candidate]:
        result = await self.db.execute(
            select(Candidate).where(
                or_(
                    Candidate.name.ilike(f"%{query_str}%"),
                    Candidate.email.ilike(f"%{query_str}%"),
                    Candidate.location.ilike(f"%{query_str}%"),
                )
            ).order_by(Candidate.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_top_candidates(self, limit: int = 10) -> list[Candidate]:
        result = await self.db.execute(
            select(Candidate)
            .join(ATSResult, Candidate.id == ATSResult.candidate_id)
            .options(selectinload(Candidate.ats_result))
            .where(Candidate.rank.in_(["gold", "silver"]))
            .order_by(ATSResult.total_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_rank(self) -> dict[str, int]:
        ranks = ["gold", "silver", "bronze", "shortlisted", "rejected", "pending"]
        counts = {}
        for rank in ranks:
            result = await self.db.execute(
                select(func.count(Candidate.id)).where(Candidate.rank == rank)
            )
            counts[rank] = result.scalar() or 0
        return counts

    async def get_analyzed_count(self) -> int:
        result = await self.db.execute(
            select(func.count(Candidate.id)).where(Candidate.status == "analyzed")
        )
        return result.scalar() or 0
