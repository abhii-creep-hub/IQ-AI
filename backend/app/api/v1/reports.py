import re
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database.session import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.candidate_service import CandidateService
from app.models.candidate import Candidate
from app.models.analysis import InterviewQuestion, ATSResult, AIAnalysis
from app.models.skill import CandidateSkill
from sqlalchemy import select

router = APIRouter(prefix="/reports", tags=["Reports"])


def _skill_name(value) -> str:
    if isinstance(value, dict):
        value = value.get("skill") or value.get("name")
    return str(value).strip() if value else ""


def _resume_evidence(raw_text: str | None, skill: str) -> list[str]:
    """Return short, verbatim resume lines that support a skill match."""
    if not raw_text or not skill:
        return []

    pattern = re.compile(rf"(?<!\w){re.escape(skill)}(?!\w)", re.IGNORECASE)
    sections = re.split(r"[\r\n]+|(?<=[.!?])\s+", raw_text[:30000])
    evidence = []
    for section in sections:
        line = re.sub(r"\s+", " ", section).strip(" \t-•")
        if line and pattern.search(line):
            if len(line) > 260:
                match = pattern.search(line)
                start = max(0, match.start() - 100)
                end = min(len(line), match.end() + 140)
                line = ("..." if start else "") + line[start:end] + ("..." if end < len(line) else "")
            evidence.append(line)
            if len(evidence) == 2:
                break
    return evidence


def _matched_skill_evidence(entries, raw_text: str | None) -> list[dict]:
    result = []
    seen = set()
    for entry in entries or []:
        skill = _skill_name(entry)
        if not skill or skill.casefold() in seen:
            continue
        seen.add(skill.casefold())
        result.append({"skill": skill, "evidence": _resume_evidence(raw_text, skill)})
    return result


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
            "matched_skill_evidence": _matched_skill_evidence(
                candidate.ats_result.matched_skills if candidate.ats_result else [],
                candidate.resume.raw_text if candidate.resume else None,
            ),
            "missing_skills": candidate.ats_result.missing_skills if candidate.ats_result else [],
            "recommended_skills": candidate.ats_result.recommended_skills if candidate.ats_result else [],
            "learning_roadmap": candidate.ats_result.learning_roadmap if candidate.ats_result else [],
        },
        "ai_analysis": {
            "match_score": candidate.ai_analysis.match_score if candidate.ai_analysis else 0,
            "hiring_recommendation": candidate.ai_analysis.hiring_recommendation if candidate.ai_analysis else "",
            "recommendation_reason": candidate.ai_analysis.recommendation_reason if candidate.ai_analysis else "",
            "skills_match": candidate.ai_analysis.skills_match if candidate.ai_analysis else {},
            "experience_match": candidate.ai_analysis.experience_match if candidate.ai_analysis else {},
            "education_match": candidate.ai_analysis.education_match if candidate.ai_analysis else {},
            "projects_match": candidate.ai_analysis.projects_match if candidate.ai_analysis else {},
            "certifications_match": candidate.ai_analysis.certifications_match if candidate.ai_analysis else {},
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


@router.get("/compare")
async def compare_candidates(
    candidate_ids: list[UUID] = Query(..., description="Two or three candidate IDs from the same job"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    unique_ids = list(dict.fromkeys(candidate_ids))
    if len(unique_ids) < 2 or len(unique_ids) > 3:
        raise HTTPException(status_code=400, detail="Select two or three candidates to compare")

    result = await db.execute(
        select(Candidate)
        .options(
            selectinload(Candidate.job),
            selectinload(Candidate.resume),
            selectinload(Candidate.skills).selectinload(CandidateSkill.skill),
            selectinload(Candidate.education),
            selectinload(Candidate.experience),
            selectinload(Candidate.ats_result),
            selectinload(Candidate.ai_analysis),
        )
        .where(Candidate.id.in_(unique_ids))
    )
    found = {candidate.id: candidate for candidate in result.scalars().all()}
    if len(found) != len(unique_ids):
        raise HTTPException(status_code=404, detail="One or more candidates could not be found")

    candidates = [found[candidate_id] for candidate_id in unique_ids]
    if len({candidate.job_id for candidate in candidates}) != 1:
        raise HTTPException(status_code=400, detail="Candidates must belong to the same job")

    job = candidates[0].job
    return {
        "job": {
            "id": str(job.id),
            "title": job.title,
            "description": job.description,
            "requirements": job.requirements,
            "required_skills": job.required_skills or [],
            "preferred_skills": job.preferred_skills or [],
        } if job else None,
        "candidates": [
            {
                "id": str(candidate.id),
                "name": candidate.name,
                "rank": candidate.rank,
                "status": candidate.status,
                "total_experience_years": candidate.total_experience_years,
                "ats_score": candidate.ats_result.total_score if candidate.ats_result else None,
                "job_match_score": candidate.ai_analysis.match_score if candidate.ai_analysis else None,
                "score_breakdown": {
                    "skills": candidate.ats_result.skills_score if candidate.ats_result else None,
                    "experience": candidate.ats_result.experience_score if candidate.ats_result else None,
                    "education": candidate.ats_result.education_score if candidate.ats_result else None,
                    "projects": candidate.ats_result.projects_score if candidate.ats_result else None,
                    "formatting": candidate.ats_result.formatting_score if candidate.ats_result else None,
                    "certifications": candidate.ats_result.certifications_score if candidate.ats_result else None,
                },
                "skills": [cs.skill.name for cs in candidate.skills if cs.skill],
                "matched_skill_evidence": _matched_skill_evidence(
                    candidate.ats_result.matched_skills if candidate.ats_result else [],
                    candidate.resume.raw_text if candidate.resume else None,
                ),
                "missing_skills": [
                    name for name in (
                        _skill_name(item)
                        for item in (candidate.ats_result.missing_skills if candidate.ats_result else [])
                    ) if name
                ],
                "experience": [
                    {
                        "title": item.title,
                        "company": item.company,
                        "start_date": item.start_date,
                        "end_date": item.end_date,
                        "is_current": item.is_current,
                    }
                    for item in candidate.experience
                ],
                "education": [
                    {
                        "degree": item.degree,
                        "field_of_study": item.field_of_study,
                        "institution": item.institution,
                    }
                    for item in candidate.education
                ],
            }
            for candidate in candidates
        ],
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
