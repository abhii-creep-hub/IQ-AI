import json
import logging
import re
from typing import Any, Optional
from openai import AsyncOpenAI
from app.core.config import settings
from app.prompts import (
    RESUME_PARSING_PROMPT,
    ATS_SCORING_PROMPT,
    JD_MATCHING_PROMPT,
    INTERVIEW_QUESTIONS_PROMPT,
    RESUME_SUMMARY_PROMPT,
    SKILL_GAP_ANALYSIS_PROMPT,
    HIRING_RECOMMENDATION_PROMPT,
)

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS

    async def _call_openai(self, prompt: str) -> dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            return self._parse_json(content)
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise

    def _parse_json(self, content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Failed to parse JSON from AI response: {content[:200]}")

    async def parse_resume(self, resume_text: str) -> dict[str, Any]:
        prompt = RESUME_PARSING_PROMPT.format(resume_text=resume_text[:12000])
        return await self._call_openai(prompt)

    async def calculate_ats_score(
        self,
        job_description: str,
        required_skills: list[str],
        preferred_skills: list[str],
        experience_min: Optional[int],
        experience_max: Optional[int],
        education_level: Optional[str],
        candidate_name: str,
        candidate_skills: list[str],
        candidate_experience: float,
        candidate_education: str,
        candidate_projects: str,
        candidate_certifications: str,
    ) -> dict[str, Any]:
        prompt = ATS_SCORING_PROMPT.format(
            job_description=job_description[:6000],
            required_skills=", ".join(required_skills) if required_skills else "Not specified",
            preferred_skills=", ".join(preferred_skills) if preferred_skills else "Not specified",
            experience_min=experience_min or "Not specified",
            experience_max=experience_max or "Not specified",
            education_level=education_level or "Not specified",
            candidate_name=candidate_name,
            candidate_skills=", ".join(candidate_skills) if candidate_skills else "None listed",
            candidate_experience=candidate_experience,
            candidate_education=candidate_education or "Not specified",
            candidate_projects=candidate_projects or "None listed",
            candidate_certifications=candidate_certifications or "None listed",
        )
        return await self._call_openai(prompt)

    async def match_jd(
        self,
        job_description: str,
        job_requirements: str,
        required_skills: list[str],
        preferred_skills: list[str],
        candidate_name: str,
        candidate_skills: list[str],
        candidate_experience: float,
        candidate_education: str,
        candidate_projects: str,
        candidate_certifications: str,
    ) -> dict[str, Any]:
        prompt = JD_MATCHING_PROMPT.format(
            job_description=job_description[:6000],
            job_requirements=job_requirements or "Not specified",
            required_skills=", ".join(required_skills) if required_skills else "Not specified",
            preferred_skills=", ".join(preferred_skills) if preferred_skills else "Not specified",
            candidate_name=candidate_name,
            candidate_skills=", ".join(candidate_skills) if candidate_skills else "None listed",
            candidate_experience=candidate_experience,
            candidate_education=candidate_education or "Not specified",
            candidate_projects=candidate_projects or "None listed",
            candidate_certifications=candidate_certifications or "None listed",
        )
        return await self._call_openai(prompt)

    async def generate_interview_questions(
        self,
        job_description: str,
        candidate_name: str,
        candidate_skills: list[str],
        candidate_experience: float,
        candidate_education: str,
        candidate_projects: str,
    ) -> dict[str, Any]:
        prompt = INTERVIEW_QUESTIONS_PROMPT.format(
            job_description=job_description[:6000],
            candidate_name=candidate_name,
            candidate_skills=", ".join(candidate_skills) if candidate_skills else "None listed",
            candidate_experience=candidate_experience,
            candidate_education=candidate_education or "Not specified",
            candidate_projects=candidate_projects or "None listed",
        )
        return await self._call_openai(prompt)

    async def generate_resume_summary(
        self,
        candidate_name: str,
        candidate_skills: list[str],
        candidate_experience: float,
        candidate_education: str,
        candidate_projects: str,
        candidate_certifications: str,
        job_title: str,
    ) -> dict[str, Any]:
        prompt = RESUME_SUMMARY_PROMPT.format(
            candidate_name=candidate_name,
            candidate_skills=", ".join(candidate_skills) if candidate_skills else "None listed",
            candidate_experience=candidate_experience,
            candidate_education=candidate_education or "Not specified",
            candidate_projects=candidate_projects or "None listed",
            candidate_certifications=candidate_certifications or "None listed",
            job_title=job_title or "Not specified",
        )
        return await self._call_openai(prompt)

    async def analyze_skill_gap(
        self,
        job_description: str,
        required_skills: list[str],
        preferred_skills: list[str],
        candidate_skills: list[str],
        candidate_experience: float,
    ) -> dict[str, Any]:
        prompt = SKILL_GAP_ANALYSIS_PROMPT.format(
            job_description=job_description[:6000],
            required_skills=", ".join(required_skills) if required_skills else "Not specified",
            preferred_skills=", ".join(preferred_skills) if preferred_skills else "Not specified",
            candidate_skills=", ".join(candidate_skills) if candidate_skills else "None listed",
            candidate_experience=candidate_experience,
        )
        return await self._call_openai(prompt)

    async def get_hiring_recommendation(
        self,
        job_title: str,
        job_description: str,
        candidate_name: str,
        ats_score: float,
        match_score: float,
        candidate_skills: list[str],
        candidate_experience: float,
    ) -> dict[str, Any]:
        prompt = HIRING_RECOMMENDATION_PROMPT.format(
            job_title=job_title or "Not specified",
            job_description=job_description[:4000],
            candidate_name=candidate_name,
            ats_score=ats_score,
            match_score=match_score,
            candidate_skills=", ".join(candidate_skills) if candidate_skills else "None listed",
            candidate_experience=candidate_experience,
        )
        return await self._call_openai(prompt)


ai_service = AIService()
