from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.candidate_service import CandidateService
from app.models.candidate import Candidate
from app.models.analysis import InterviewQuestion, ATSResult, AIAnalysis
from sqlalchemy import select

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/candidate/{candidate_id}/full")
async def get_full_candidate_report(
    candidate_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CandidateService(db)
    candidate = await service.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    questions_result = await db.execute(
        select(InterviewQuestion).where(InterviewQuestion.candidate_id == candidate_id)
    )
    questions = questions_result.scalars().all()

    return {
        "candidate": {
            "id": str(candidate.id),
            "name": candidate.name,
            "email": candidate.email,
            "phone": candidate.phone,
            "location": candidate.location,
            "rank": candidate.rank,
            "status": candidate.status,
            "total_experience_years": candidate.total_experience_years,
            "hiring_recommendation": candidate.hiring_recommendation,
        },
        "summary": {
            "ai_summary": candidate.ai_summary,
            "strengths": candidate.ai_strengths or [],
            "weaknesses": candidate.ai_weaknesses or [],
            "career_highlights": candidate.ai_career_highlights or [],
        },
        "ats_result": {
            "total_score": candidate.ats_result.total_score if candidate.ats_result else 0,
            "skills_score": candidate.ats_result.skills_score if candidate.ats_result else 0,
            "experience_score": candidate.ats_result.experience_score if candidate.ats_result else 0,
            "education_score": candidate.ats_result.education_score if candidate.ats_result else 0,
            "projects_score": candidate.ats_result.projects_score if candidate.ats_result else 0,
            "formatting_score": candidate.ats_result.formatting_score if candidate.ats_result else 0,
            "certifications_score": candidate.ats_result.certifications_score if candidate.ats_result else 0,
            "matched_skills": candidate.ats_result.matched_skills if candidate.ats_result else [],
            "missing_skills": candidate.ats_result.missing_skills if candidate.ats_result else [],
            "recommended_skills": candidate.ats_result.recommended_skills if candidate.ats_result else [],
            "learning_roadmap": candidate.ats_result.learning_roadmap if candidate.ats_result else [],
        },
        "ai_analysis": {
            "match_score": candidate.ai_analysis.match_score if candidate.ai_analysis else 0,
            "hiring_recommendation": candidate.ai_analysis.hiring_recommendation if candidate.ai_analysis else "",
            "recommendation_reason": candidate.ai_analysis.recommendation_reason if candidate.ai_analysis else "",
        },
        "interview_questions": [
            {
                "question": q.question,
                "category": q.category,
                "difficulty": q.difficulty,
                "expected_answer": q.expected_answer,
            }
            for q in questions
        ],
        "skills": [
            {"name": cs.skill.name, "proficiency": cs.proficiency}
            for cs in candidate.skills if cs.skill
        ] if candidate.skills else [],
        "education": [
            {
                "institution": e.institution,
                "degree": e.degree,
                "field_of_study": e.field_of_study,
                "start_year": e.start_year,
                "end_year": e.end_year,
            }
            for e in candidate.education
        ] if candidate.education else [],
        "experience": [
            {
                "company": exp.company,
                "title": exp.title,
                "location": exp.location,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "description": exp.description,
            }
            for exp in candidate.experience
        ] if candidate.experience else [],
    }


@router.get("/ranking")
async def get_ranking_report(
    job_id: UUID = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CandidateService(db)
    if job_id:
        candidates = await service.list_by_job(job_id)
    else:
        candidates = await service.list_candidates(0, 1000)

    ranked = sorted(candidates, key=lambda c: c.rank)
    rank_order = {"gold": 0, "silver": 1, "bronze": 2, "shortlisted": 3, "pending": 4, "rejected": 5}
    ranked.sort(key=lambda c: rank_order.get(c.rank, 99))

    return {
        "candidates": [
            {
                "id": str(c.id),
                "name": c.name,
                "email": c.email,
                "rank": c.rank,
                "status": c.status,
                "hiring_recommendation": c.hiring_recommendation,
                "ats_score": c.ats_result.total_score if c.ats_result else None,
            }
            for c in ranked
        ],
        "summary": {
            "total": len(ranked),
            "gold": len([c for c in ranked if c.rank == "gold"]),
            "silver": len([c for c in ranked if c.rank == "silver"]),
            "bronze": len([c for c in ranked if c.rank == "bronze"]),
            "shortlisted": len([c for c in ranked if c.rank == "shortlisted"]),
            "pending": len([c for c in ranked if c.rank == "pending"]),
            "rejected": len([c for c in ranked if c.rank == "rejected"]),
        },
    }
