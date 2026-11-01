from typing import Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.job import Job


class JobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, job_id: UUID) -> Optional[Job]:
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def create(self, job: Job) -> Job:
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def update(self, job: Job) -> Job:
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def delete(self, job_id: UUID) -> bool:
        job = await self.get_by_id(job_id)
        if job:
            await self.db.delete(job)
            await self.db.commit()
            return True
        return False

    async def list_by_owner(self, owner_id: UUID, skip: int = 0, limit: int = 100) -> list[Job]:
        result = await self.db.execute(
            select(Job)
            .options(selectinload(Job.candidates))
            .where(Job.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .order_by(Job.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[Job]:
        result = await self.db.execute(
            select(Job)
            .options(selectinload(Job.candidates))
            .offset(skip)
            .limit(limit)
            .order_by(Job.created_at.desc())
        )
        return list(result.scalars().all())

    async def count(self, owner_id: Optional[UUID] = None) -> int:
        query = select(func.count(Job.id))
        if owner_id:
            query = query.where(Job.owner_id == owner_id)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def search(self, query_str: str, owner_id: Optional[UUID] = None) -> list[Job]:
        query = select(Job).where(
            Job.title.ilike(f"%{query_str}%")
            | Job.description.ilike(f"%{query_str}%")
        ).options(selectinload(Job.candidates))
        if owner_id:
            query = query.where(Job.owner_id == owner_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())
