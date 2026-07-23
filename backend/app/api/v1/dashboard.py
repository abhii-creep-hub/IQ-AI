from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.candidate_service import CandidateService
from app.services.job_service import JobService
from app.repositories.candidate_repo import CandidateRepository

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    candidate_service = CandidateService(db)
    job_service = JobService(db)

    stats = await candidate_service.get_dashboard_stats()
    total_jobs = await job_service.count_jobs(current_user.id)

    return {
        "total_candidates": stats["total_candidates"],
        "total_jobs": total_jobs,
        "analyzed_count": stats["analyzed_count"],
        "gold_count": stats["rank_counts"].get("gold", 0),
        "silver_count": stats["rank_counts"].get("silver", 0),
        "bronze_count": stats["rank_counts"].get("bronze", 0),
        "shortlisted_count": stats["rank_counts"].get("shortlisted", 0),
        "rejected_count": stats["rank_counts"].get("rejected", 0),
        "pending_count": stats["rank_counts"].get("pending", 0),
        "top_candidates": stats["top_candidates"],
        "hiring_funnel": [
            {"name": "Uploaded", "value": stats["total_candidates"]},
            {"name": "Analyzed", "value": stats["analyzed_count"]},
            {"name": "Gold", "value": stats["rank_counts"].get("gold", 0)},
            {"name": "Silver", "value": stats["rank_counts"].get("silver", 0)},
            {"name": "Shortlisted", "value": stats["rank_counts"].get("shortlisted", 0)},
            {"name": "Rejected", "value": stats["rank_counts"].get("rejected", 0)},
        ],
        "score_distribution": [
            {"range": "90-100", "count": 0},
            {"range": "80-89", "count": 0},
            {"range": "70-79", "count": 0},
            {"range": "60-69", "count": 0},
            {"range": "50-59", "count": 0},
            {"range": "Below 50", "count": 0},
        ],
        "recent_uploads": [],
        "skill_distribution": [],
        "upload_trend": [],
    }


@router.get("/analytics/skills")
async def get_skill_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select, func
    from app.models.skill import Skill, CandidateSkill

    result = await db.execute(
        select(Skill.name, func.count(CandidateSkill.id).label("count"))
        .join(CandidateSkill, Skill.id == CandidateSkill.skill_id)
        .group_by(Skill.name)
        .order_by(func.count(CandidateSkill.id).desc())
        .limit(20)
    )
    skills = [{"name": row[0], "count": row[1]} for row in result.all()]
    return {"skills": skills}


@router.get("/analytics/ranks")
async def get_rank_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = CandidateRepository(db)
    counts = await repo.count_by_rank()
    return {"ranks": counts}
