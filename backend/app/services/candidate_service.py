import os
import logging
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.models.candidate import Candidate
from app.models.resume import Resume
from app.models.skill import Skill, CandidateSkill
from app.models.education_experience import Education, Experience, Project, Certification
from app.models.analysis import ATSResult, AIAnalysis, InterviewQuestion
from app.repositories.candidate_repo import CandidateRepository
from app.ai.service import ai_service
from app.ai.parser import extract_text, clean_resume_text, calculate_total_experience, determine_rank
from app.core.config import settings

logger = logging.getLogger(__name__)


class CandidateService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CandidateRepository(db)

    async def upload_resume(self, user_id: UUID, file_content: bytes, filename: str, file_type: str, job_id: Optional[UUID] = None) -> dict:
        candidate = Candidate(name="Pending", status="uploaded", rank="pending", job_id=job_id)
        candidate = await self.repo.create(candidate)

        file_id = uuid4()
        ext = file_type.lower().replace(".", "")
        save_name = f"{file_id}.{ext}"
        upload_dir = os.path.join(settings.UPLOAD_DIR, "resumes")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, save_name)
        with open(file_path, "wb") as f:
            f.write(file_content)

        resume = Resume(
            filename=save_name,
            original_filename=filename,
            file_path=file_path,
            file_size=len(file_content),
            file_type=ext,
            status="uploaded",
            candidate_id=candidate.id,
            uploaded_by=user_id,
        )
        self.db.add(resume)
        await self.db.commit()
        await self.db.refresh(resume)
        await self.db.refresh(candidate)

        return {"candidate_id": str(candidate.id), "resume_id": str(resume.id), "status": "uploaded"}

    async def parse_resume(self, candidate_id: UUID) -> dict:
        candidate = await self.repo.get_by_id(candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")
        resume = candidate.resume
        if not resume:
            raise ValueError("Resume not found")

        resume.status = "parsing"
        candidate.status = "parsing"
        await self.db.commit()

        try:
            with open(resume.file_path, "rb") as f:
                file_content = f.read()
            raw_text = extract_text(file_content, resume.file_type)
            if not raw_text:
                raise ValueError("Could not extract text from resume")
            cleaned_text = clean_resume_text(raw_text)
            resume.raw_text = cleaned_text

            parsed_data = await ai_service.parse_resume(cleaned_text)
            resume.parsed_data = parsed_data
            resume.status = "parsed"

            candidate.name = parsed_data.get("name", candidate.name)
            candidate.email = parsed_data.get("email")
            candidate.phone = parsed_data.get("phone")
            candidate.location = parsed_data.get("location")
            candidate.linkedin_url = parsed_data.get("linkedin_url")
            candidate.github_url = parsed_data.get("github_url")
            candidate.portfolio_url = parsed_data.get("portfolio_url")
            candidate.status = "parsed"

            for edu_data in parsed_data.get("education", []):
                edu = Education(
                    candidate_id=candidate.id,
                    institution=edu_data.get("institution", ""),
                    degree=edu_data.get("degree"),
                    field_of_study=edu_data.get("field_of_study"),
                    start_year=edu_data.get("start_year"),
                    end_year=edu_data.get("end_year"),
                    gpa=edu_data.get("gpa"),
                    description=edu_data.get("description"),
                )
                self.db.add(edu)

            for exp_data in parsed_data.get("experience", []):
                exp = Experience(
                    candidate_id=candidate.id,
                    company=exp_data.get("company", ""),
                    title=exp_data.get("title", ""),
                    location=exp_data.get("location"),
                    start_date=exp_data.get("start_date"),
                    end_date=exp_data.get("end_date"),
                    is_current=exp_data.get("is_current", "false"),
                    description=exp_data.get("description"),
                    achievements=exp_data.get("achievements", []),
                )
                self.db.add(exp)

            for proj_data in parsed_data.get("projects", []):
                proj = Project(
                    candidate_id=candidate.id,
                    name=proj_data.get("name", ""),
                    description=proj_data.get("description"),
                    technologies=proj_data.get("technologies", []),
                    url=proj_data.get("url"),
                    github_url=proj_data.get("github_url"),
                )
                self.db.add(proj)

            for cert_data in parsed_data.get("certifications", []):
                cert = Certification(
                    candidate_id=candidate.id,
                    name=cert_data.get("name", ""),
                    issuer=cert_data.get("issuer"),
                    date_obtained=cert_data.get("date_obtained"),
                    expiry_date=cert_data.get("expiry_date"),
                    credential_url=cert_data.get("credential_url"),
                )
                self.db.add(cert)

            for skill_name in parsed_data.get("skills", []):
                skill_result = await self.db.execute(
                    select(Skill).where(Skill.name.ilike(skill_name))
                )
                skill = skill_result.scalar_one_or_none()
                if not skill:
                    skill = Skill(name=skill_name)
                    self.db.add(skill)
                    await self.db.flush()
                cs = CandidateSkill(candidate_id=candidate.id, skill_id=skill.id)
                self.db.add(cs)

            experience_list = parsed_data.get("experience", [])
            candidate.total_experience_years = calculate_total_experience(experience_list) or parsed_data.get("total_experience_years", 0.0)

            await self.db.commit()
            return {"status": "parsed", "name": candidate.name, "skills_count": len(parsed_data.get("skills", []))}

        except Exception as e:
            logger.error(f"Resume parsing failed for {candidate_id}: {str(e)}")
            resume.status = "error"
            resume.parsing_error = str(e)
            candidate.status = "error"
            await self.db.commit()
            raise

    async def analyze_candidate(self, candidate_id: UUID, job_id: Optional[UUID] = None) -> dict:
        candidate = await self.repo.get_by_id(candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")

        if candidate.status not in ("parsed", "analyzed"):
            raise ValueError("Resume must be parsed before analysis")

        candidate.status = "analyzing"
        await self.db.commit()

        try:
            job_description = ""
            required_skills = []
            preferred_skills = []
            experience_min = None
            experience_max = None
            education_level = None
            job_title = "Not specified"

            if job_id:
                from app.models.job import Job
                job_result = await self.db.execute(select(Job).where(Job.id == job_id))
                job = job_result.scalar_one_or_none()
                if job:
                    job_description = job.description or ""
                    required_skills = job.required_skills or []
                    preferred_skills = job.preferred_skills or []
                    experience_min = job.experience_min
                    experience_max = job.experience_max
                    education_level = job.education_level
                    job_title = job.title
                    if not candidate.job_id:
                        candidate.job_id = job_id

            candidate_skills = [
                cs.skill.name for cs in candidate.skills if cs.skill
            ] if candidate.skills else []
            candidate_education = "; ".join(
                [f"{e.degree} in {e.field_of_study} from {e.institution}" for e in candidate.education]
            ) if candidate.education else ""
            candidate_projects = "; ".join(
                [f"{p.name}: {p.description or ''}" for p in candidate.projects]
            ) if candidate.projects else ""
            candidate_certifications = "; ".join(
                [f"{c.name} ({c.issuer or ''})" for c in candidate.certifications]
            ) if candidate.certifications else ""
            candidate_experience = candidate.total_experience_years or 0.0

            ats_data = await ai_service.calculate_ats_score(
                job_description=job_description,
                required_skills=required_skills,
                preferred_skills=preferred_skills,
                experience_min=experience_min,
                experience_max=experience_max,
                education_level=education_level,
                candidate_name=candidate.name,
                candidate_skills=candidate_skills,
                candidate_experience=candidate_experience,
                candidate_education=candidate_education,
                candidate_projects=candidate_projects,
                candidate_certifications=candidate_certifications,
            )

            existing_ats = await self.db.execute(
                select(ATSResult).where(ATSResult.candidate_id == candidate_id)
            )
            ats_result = existing_ats.scalar_one_or_none()
            if ats_result:
                for key, value in ats_data.items():
                    if hasattr(ats_result, key):
                        setattr(ats_result, key, value)
            else:
                ats_result = ATSResult(candidate_id=candidate_id, **ats_data)
                self.db.add(ats_result)

            summary_data = await ai_service.generate_resume_summary(
                candidate_name=candidate.name,
                candidate_skills=candidate_skills,
                candidate_experience=candidate_experience,
                candidate_education=candidate_education,
                candidate_projects=candidate_projects,
                candidate_certifications=candidate_certifications,
                job_title=job_title,
            )
            candidate.ai_summary = summary_data.get("summary", "")
            candidate.ai_strengths = summary_data.get("strengths", [])
            candidate.ai_weaknesses = summary_data.get("weaknesses", [])
            candidate.ai_career_highlights = summary_data.get("career_highlights", [])

            match_data = await ai_service.match_jd(
                job_description=job_description,
                job_requirements=job_description,
                required_skills=required_skills,
                preferred_skills=preferred_skills,
                candidate_name=candidate.name,
                candidate_skills=candidate_skills,
                candidate_experience=candidate_experience,
                candidate_education=candidate_education,
                candidate_projects=candidate_projects,
                candidate_certifications=candidate_certifications,
            )

            existing_analysis = await self.db.execute(
                select(AIAnalysis).where(AIAnalysis.candidate_id == candidate_id)
            )
            analysis = existing_analysis.scalar_one_or_none()
            if analysis:
                analysis.match_score = match_data.get("match_score", 0)
                analysis.skills_match = match_data.get("skills_match", {})
                analysis.education_match = match_data.get("education_match", {})
                analysis.experience_match = match_data.get("experience_match", {})
                analysis.projects_match = match_data.get("projects_match", {})
                analysis.certifications_match = match_data.get("certifications_match", {})
            else:
                analysis = AIAnalysis(
                    candidate_id=candidate_id,
                    match_score=match_data.get("match_score", 0),
                    skills_match=match_data.get("skills_match", {}),
                    education_match=match_data.get("education_match", {}),
                    experience_match=match_data.get("experience_match", {}),
                    projects_match=match_data.get("projects_match", {}),
                    certifications_match=match_data.get("certifications_match", {}),
                )
                self.db.add(analysis)

            recommendation_data = await ai_service.get_hiring_recommendation(
                job_title=job_title,
                job_description=job_description,
                candidate_name=candidate.name,
                ats_score=ats_data.get("total_score", 0),
                match_score=match_data.get("match_score", 0),
                candidate_skills=candidate_skills,
                candidate_experience=candidate_experience,
            )
            analysis.summary = recommendation_data.get("reasoning", "")
            analysis.strengths = recommendation_data.get("key_strengths", [])
            analysis.weaknesses = recommendation_data.get("key_concerns", [])
            analysis.hiring_recommendation = recommendation_data.get("recommendation", "")
            analysis.recommendation_reason = recommendation_data.get("reasoning", "")
            candidate.hiring_recommendation = recommendation_data.get("recommendation", "")

            ats_total = ats_data.get("total_score", 0)
            match_score = match_data.get("match_score", 0)
            candidate.rank = determine_rank(ats_total, match_score)
            candidate.status = "analyzed"

            skill_gap_data = await ai_service.analyze_skill_gap(
                job_description=job_description,
                required_skills=required_skills,
                preferred_skills=preferred_skills,
                candidate_skills=candidate_skills,
                candidate_experience=candidate_experience,
            )
            ats_result.matched_skills = skill_gap_data.get("matched_skills", [])
            ats_result.missing_skills = skill_gap_data.get("missing_skills", [])
            ats_result.recommended_skills = skill_gap_data.get("recommended_skills", [])
            ats_result.learning_roadmap = skill_gap_data.get("learning_roadmap", [])

            questions_data = await ai_service.generate_interview_questions(
                job_description=job_description,
                candidate_name=candidate.name,
                candidate_skills=candidate_skills,
                candidate_experience=candidate_experience,
                candidate_education=candidate_education,
                candidate_projects=candidate_projects,
            )
            for q in questions_data.get("questions", []):
                question = InterviewQuestion(
                    candidate_id=candidate_id,
                    question=q.get("question", ""),
                    category=q.get("category", "technical"),
                    difficulty=q.get("difficulty", "medium"),
                    expected_answer=q.get("expected_answer"),
                )
                self.db.add(question)

            await self.db.commit()

            return {
                "ats_score": ats_total,
                "match_score": match_score,
                "rank": candidate.rank,
                "recommendation": candidate.hiring_recommendation,
            }

        except Exception as e:
            logger.error(f"Analysis failed for {candidate_id}: {str(e)}")
            candidate.status = "error"
            await self.db.commit()
            raise

    async def get_candidate(self, candidate_id: UUID) -> Optional[Candidate]:
        return await self.repo.get_by_id(candidate_id)

    async def list_candidates(self, skip: int = 0, limit: int = 100) -> list[Candidate]:
        return await self.repo.list_with_relations(skip, limit)

    async def list_by_job(self, job_id: UUID, skip: int = 0, limit: int = 100) -> list[Candidate]:
        return await self.repo.list_by_job(job_id, skip, limit)

    async def search_candidates(self, query: str) -> list[Candidate]:
        return await self.repo.search(query)

    async def update_candidate(self, candidate_id: UUID, **kwargs) -> Candidate:
        candidate = await self.repo.get_by_id(candidate_id)
        if not candidate:
            raise ValueError("Candidate not found")
        for key, value in kwargs.items():
            if value is not None and hasattr(candidate, key):
                setattr(candidate, key, value)
        return await self.repo.update(candidate)

    async def delete_candidate(self, candidate_id: UUID) -> bool:
        return await self.repo.delete(candidate_id)

    async def count_candidates(self) -> int:
        return await self.repo.count()

    async def get_dashboard_stats(self) -> dict:
        total = await self.repo.count()
        analyzed = await self.repo.get_analyzed_count()
        rank_counts = await self.repo.count_by_rank()
        top = await self.repo.get_top_candidates(10)
        return {
            "total_candidates": total,
            "analyzed_count": analyzed,
            "rank_counts": rank_counts,
            "top_candidates": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "rank": c.rank,
                    "ats_score": c.ats_result.total_score if c.ats_result else 0,
                }
                for c in top
            ],
        }
