from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import AliasChoices, AliasPath, BaseModel, Field


class EducationSchema(BaseModel):
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    gpa: Optional[str] = None
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class ExperienceSchema(BaseModel):
    company: str
    title: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: Optional[str] = "false"
    description: Optional[str] = None
    achievements: Optional[List[str]] = []

    model_config = {"from_attributes": True}


class ProjectSchema(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: Optional[List[str]] = []
    url: Optional[str] = None
    github_url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    model_config = {"from_attributes": True}


class CertificationSchema(BaseModel):
    name: str
    issuer: Optional[str] = None
    date_obtained: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_url: Optional[str] = None

    model_config = {"from_attributes": True}


class CandidateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    total_experience_years: Optional[float] = None


class CandidateCreate(CandidateBase):
    job_id: Optional[UUID] = None


class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    total_experience_years: Optional[float] = None
    rank: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    job_id: Optional[UUID] = None


class SkillSchema(BaseModel):
    name: str = Field(validation_alias=AliasChoices("name", AliasPath("skill", "name")))
    category: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("category", AliasPath("skill", "category")),
    )
    proficiency: Optional[str] = None
    years_experience: Optional[float] = None

    model_config = {"from_attributes": True}


class CandidateResponse(CandidateBase):
    id: UUID
    rank: str
    status: str
    ai_summary: Optional[str] = None
    ai_strengths: Optional[List[str]] = []
    ai_weaknesses: Optional[List[str]] = []
    hiring_recommendation: Optional[str] = None
    job_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CandidateDetailResponse(CandidateResponse):
    skills: Optional[List[SkillSchema]] = []
    education: Optional[List[EducationSchema]] = []
    experience: Optional[List[ExperienceSchema]] = []
    projects: Optional[List[ProjectSchema]] = []
    certifications: Optional[List[CertificationSchema]] = []


class ResumeUploadResponse(BaseModel):
    id: UUID
    filename: str
    status: str
    candidate_id: UUID
    message: str = "Resume uploaded successfully"


class ResumeAnalysisResponse(BaseModel):
    candidate_id: UUID
    ats_score: float
    match_score: float
    rank: str
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    missing_skills: List[str]
    recommended_skills: List[str]
    interview_questions_count: int
    hiring_recommendation: str


class DashboardStats(BaseModel):
    total_candidates: int = 0
    total_jobs: int = 0
    total_resumes: int = 0
    analyzed_count: int = 0
    avg_ats_score: float = 0.0
    gold_count: int = 0
    silver_count: int = 0
    bronze_count: int = 0
    shortlisted_count: int = 0
    rejected_count: int = 0
    pending_count: int = 0
    recent_uploads: List = []
    top_candidates: List = []
    skill_distribution: List = []
    hiring_funnel: List = []
    score_distribution: List = []
    upload_trend: List = []


class ReportGenerateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    report_type: str = "candidates"
    format: str = "pdf"
    job_id: Optional[UUID] = None
    candidate_ids: Optional[List[UUID]] = []
    filters: Optional[dict] = None


class ReportResponse(BaseModel):
    id: UUID
    title: str
    report_type: str
    format: str
    file_path: Optional[str] = None
    file_size: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityLogResponse(BaseModel):
    id: UUID
    action: str
    resource_type: Optional[str] = None
    details: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}
