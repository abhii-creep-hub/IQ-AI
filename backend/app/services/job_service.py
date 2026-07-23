from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import Job
from app.repositories.job_repo import JobRepository


class JobService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = JobRepository(db)

    async def create_job(self, owner_id: UUID, **kwargs) -> Job:
        job = Job(owner_id=owner_id, **kwargs)
        return await self.repo.create(job)

    async def get_job(self, job_id: UUID) -> Optional[Job]:
        return await self.repo.get_by_id(job_id)

    async def update_job(self, job_id: UUID, **kwargs) -> Job:
        job = await self.repo.get_by_id(job_id)
        if not job:
            raise ValueError("Job not found")
        for key, value in kwargs.items():
            if value is not None and hasattr(job, key):
                setattr(job, key, value)
        return await self.repo.update(job)

    async def delete_job(self, job_id: UUID) -> bool:
        return await self.repo.delete(job_id)

    async def list_jobs(self, owner_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> list[Job]:
        if owner_id:
            return await self.repo.list_by_owner(owner_id, skip, limit)
        return await self.repo.list_all(skip, limit)

    async def count_jobs(self, owner_id: Optional[UUID] = None) -> int:
        return await self.repo.count(owner_id)

    async def search_jobs(self, query: str, owner_id: Optional[UUID] = None) -> list[Job]:
        return await self.repo.search(query, owner_id)
